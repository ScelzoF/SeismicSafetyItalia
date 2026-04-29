import os
import re
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import streamlit as st
import defusedxml.ElementTree as ET  # sicuro contro XXE/XML-bomb attacks
from concurrent.futures import ThreadPoolExecutor, as_completed

INGV_API_URL = "https://webservices.ingv.it/fdsnws/event/1/query"
USGS_API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
REQUEST_TIMEOUT = 6


def _retry_get(url, params=None, headers=None, timeout=REQUEST_TIMEOUT, max_retries=3):
    """requests.get con retry automatico — backoff esponenziale su 5xx/timeout."""
    import time as _time
    last_exc = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                _time.sleep(0.8 * (2 ** attempt))
                continue
            return resp
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError) as exc:
            last_exc = exc
            _time.sleep(0.8 * (2 ** attempt))
    if last_exc:
        raise last_exc
    return resp


def _ingv_ov_get(url, timeout=8, **kwargs):
    """GET con SSL fallback per endpoint INGV OV (certificati talvolta problematici).
    Tenta prima con verify=True; se SSLError ritenta con verify=False (solo rete INGV)."""
    import warnings as _w
    try:
        return requests.get(url, timeout=timeout, **kwargs)
    except requests.exceptions.SSLError:
        _w.warn(f"SSLError su {url} — retry senza verifica cert (INGV OV)", stacklevel=2)
        return requests.get(url, timeout=timeout, verify=False, **kwargs)  # nosec B501

INGV_OV_RSS = "https://www.ov.ingv.it/index.php/it/news-ov?format=feed&type=rss"
INGV_NEWS_RSS = "https://www.ingv.it/feed/"

_FALLBACK_PATH = os.path.join(os.path.dirname(__file__), "data", "earthquake_cache.json")


def _save_fallback(df):
    try:
        os.makedirs(os.path.dirname(_FALLBACK_PATH), exist_ok=True)
        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
            df_copy[col] = df_copy[col].astype(str)
        df_copy.to_json(_FALLBACK_PATH, orient="records", date_format="iso")
    except Exception:
        pass


def _load_fallback():
    try:
        if os.path.exists(_FALLBACK_PATH):
            df = pd.read_json(_FALLBACK_PATH, orient="records")
            if not df.empty and "time" in df.columns:
                df["datetime"] = pd.to_datetime(df.get("datetime", df["time"]), errors="coerce")
                df = df.dropna(subset=["datetime"])
                return df, True
    except Exception:
        pass
    return pd.DataFrame(), False


def _fetch_ingv_raw():
    """Fetch INGV data — 7 giorni — Italia."""
    end_time = datetime.utcnow().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(days=7)
    params = {
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmag": 1.0,
        "maxlat": 48.0, "minlat": 35.0,
        "maxlon": 19.0, "minlon": 6.0,
        "format": "geojson",
        "limit": 500
    }
    headers = {"Accept": "application/json", "User-Agent": "SeismicSafetyItalia/2.0"}
    resp = _retry_get(INGV_API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200 or not resp.text:
        return pd.DataFrame()
    data = resp.json()
    earthquakes = []
    for event in data.get("features", []):
        props = event.get("properties", {})
        coords = (event.get("geometry") or {}).get("coordinates", [0, 0, 0])
        time_val = props.get("time", "")
        if isinstance(time_val, (int, float)):
            time_str = datetime.utcfromtimestamp(time_val / 1000).strftime("%Y-%m-%dT%H:%M:%S")
        else:
            time_str = str(time_val)
        earthquakes.append({
            "time": time_str,
            "magnitude": float(props.get("mag") or 0),
            "depth": float(coords[2]) if len(coords) > 2 else 0.0,
            "latitude": float(coords[1]) if len(coords) > 1 else 0.0,
            "longitude": float(coords[0]) if len(coords) > 0 else 0.0,
            "location": str(props.get("place") or "Sconosciuta"),
            "source": "INGV"
        })
    return pd.DataFrame(earthquakes)


def _fetch_usgs_raw():
    """Fetch USGS data — 7 giorni — Campania ±100km."""
    end_time = datetime.utcnow().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(days=7)
    params = {
        "format": "geojson",
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": 1.0,
        "latitude": 40.85, "longitude": 14.25,
        "maxradiuskm": 100,
        "limit": 500
    }
    headers = {"Accept": "application/json", "User-Agent": "SeismicSafetyItalia/2.0"}
    resp = _retry_get(USGS_API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    if resp.status_code != 200 or not resp.text:
        return pd.DataFrame()
    data = resp.json()
    features = data.get("features", [])
    if not features:
        return pd.DataFrame()
    rows = []
    for f in features:
        if not f.get("properties") or not f.get("geometry"):
            continue
        coords = f["geometry"].get("coordinates", [0, 0, 0])
        t = f["properties"].get("time", 0)
        rows.append({
            "time": datetime.utcfromtimestamp((t or 0) / 1000).strftime("%Y-%m-%dT%H:%M:%S"),
            "magnitude": float(f["properties"].get("mag") or 0),
            "depth": float(coords[2]) if len(coords) > 2 else 0.0,
            "latitude": float(coords[1]) if len(coords) > 1 else 0.0,
            "longitude": float(coords[0]) if len(coords) > 0 else 0.0,
            "location": str(f["properties"].get("place") or "Sconosciuta"),
            "source": "USGS"
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_ingv_data():
    """INGV — con fallback su disco."""
    try:
        df = _fetch_ingv_raw()
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_earthquake_data_for_ml(days: int = 30) -> "pd.DataFrame":
    """
    Fetch INGV su finestra estesa (default 30 giorni) per il modello ML.
    Cache separata (TTL 1 ora) per non appesantire il refresh normale (15 min).
    """
    try:
        end_time = datetime.utcnow().replace(second=0, microsecond=0)
        start_time = end_time - timedelta(days=days)
        params = {
            "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime":   end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "minmag": 1.0,
            "maxlat": 48.0, "minlat": 35.0,
            "maxlon": 19.0, "minlon": 6.0,
            "format": "geojson",
            "limit": 2000,
        }
        headers = {"Accept": "application/json", "User-Agent": "SeismicSafetyItalia/2.0"}
        resp = _retry_get(INGV_API_URL, params=params, headers=headers, timeout=15)
        if resp.status_code != 200 or not resp.text:
            return pd.DataFrame()
        data = resp.json()
        rows = []
        for event in data.get("features", []):
            props  = event.get("properties", {})
            coords = (event.get("geometry") or {}).get("coordinates", [0, 0, 0])
            time_val = props.get("time", "")
            if isinstance(time_val, (int, float)):
                time_str = datetime.utcfromtimestamp(time_val / 1000).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                time_str = str(time_val)
            rows.append({
                "time":      time_str,
                "magnitude": float(props.get("mag") or 0),
                "depth":     float(coords[2]) if len(coords) > 2 else 0.0,
                "latitude":  float(coords[1]) if len(coords) > 1 else 0.0,
                "longitude": float(coords[0]) if len(coords) > 0 else 0.0,
                "location":  str(props.get("place") or "Sconosciuta"),
                "source":    "INGV",
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            # Normalizza colonna datetime come fa fetch_earthquake_data()
            df["datetime"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.dropna(subset=["datetime"])
            df = df.sort_values("datetime", ascending=False)
        return df
    except Exception:
        return pd.DataFrame()


# Bounds allargati per aree vulcaniche (copertura rete locale OV)
_VOLCANIC_BOUNDS = {
    "vesuvio":       {"minlat": 40.70, "maxlat": 40.95, "minlon": 14.25, "maxlon": 14.65},
    "campi_flegrei": {"minlat": 40.73, "maxlat": 40.97, "minlon": 13.85, "maxlon": 14.30},
    "ischia":        {"minlat": 40.65, "maxlat": 40.85, "minlon": 13.80, "maxlon": 14.05},
}


@st.cache_data(ttl=10800, show_spinner=False)
def fetch_earthquake_data_for_ml_area(area_key: str, days: int = 90) -> "pd.DataFrame":
    """
    Fetch INGV su finestra 90 giorni per aree vulcaniche campane.
    Box allargato rispetto a filter_area_earthquakes, soglia M0.0.
    Cache TTL 3 ore per non appesantire l'API.
    """
    bounds = _VOLCANIC_BOUNDS.get(area_key)
    if not bounds:
        return pd.DataFrame()
    try:
        end_time = datetime.utcnow().replace(second=0, microsecond=0)
        start_time = end_time - timedelta(days=days)
        params = {
            "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime":   end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "minmag": 0.0,
            "format": "geojson",
            "limit": 5000,
            **bounds,
        }
        headers = {"Accept": "application/json", "User-Agent": "SeismicSafetyItalia/2.0"}
        resp = _retry_get(INGV_API_URL, params=params, headers=headers, timeout=20)
        if resp.status_code != 200 or not resp.text:
            return pd.DataFrame()
        data = resp.json()
        rows = []
        for event in data.get("features", []):
            props  = event.get("properties", {})
            coords = (event.get("geometry") or {}).get("coordinates", [0, 0, 0])
            time_val = props.get("time", "")
            if isinstance(time_val, (int, float)):
                time_str = datetime.utcfromtimestamp(time_val / 1000).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                time_str = str(time_val)
            rows.append({
                "time":      time_str,
                "magnitude": float(props.get("mag") or 0),
                "depth":     float(coords[2]) if len(coords) > 2 else 0.0,
                "latitude":  float(coords[1]) if len(coords) > 1 else 0.0,
                "longitude": float(coords[0]) if len(coords) > 0 else 0.0,
                "location":  str(props.get("place") or "Sconosciuta"),
                "source":    "INGV",
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.dropna(subset=["datetime"])
            df = df.sort_values("datetime", ascending=False)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=900, show_spinner=False)
def fetch_usgs_data():
    """USGS — con fallback su disco."""
    try:
        df = _fetch_usgs_raw()
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()


def _fetch_emsc_raw():
    """Fetch EMSC data — 7 giorni — Italia (European Mediterranean Seismological Centre)."""
    end_time = datetime.utcnow().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(days=7)
    params = {
        "format": "json",
        "start":  start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "end":    end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmag": 1.0,
        "minlat": 35.0, "maxlat": 48.0,
        "minlon": 6.0,  "maxlon": 19.0,
        "limit":  500,
    }
    headers = {"Accept": "application/json", "User-Agent": "SeismicSafetyItalia/2.0"}
    try:
        resp = _retry_get(
            "https://www.seismicportal.eu/fdsnws/event/1/query",
            params=params, headers=headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code != 200 or not resp.text:
            return pd.DataFrame()
        data = resp.json()
        rows = []
        for feature in data.get("features", []):
            props  = feature.get("properties", {})
            coords = (feature.get("geometry") or {}).get("coordinates", [0, 0, 0])
            t      = props.get("time") or props.get("lastupdate", "")
            if not t:
                continue
            rows.append({
                "time":      str(t)[:19],
                "magnitude": float(props.get("mag") or 0),
                "depth":     float(coords[2]) if len(coords) > 2 else 0.0,
                "latitude":  float(coords[1]) if len(coords) > 1 else 0.0,
                "longitude": float(coords[0]) if len(coords) > 0 else 0.0,
                "location":  str(props.get("flynn_region") or props.get("place") or "Sconosciuta"),
                "source":    "EMSC",
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def _fetch_gossip_raw():
    """
    GOSSIP INGV OV — catalogo sismico vulcani campani (Vesuvio, CF, Ischia).
    Feed RSS aggiornato ogni 60 secondi. Complementare a INGV FDSNWS:
    la rete locale OV rileva eventi molto piccoli non nel catalogo FDSN.
    """
    try:
        r = _ingv_ov_get(
            "https://terremoti.ov.ingv.it/gossip/report.xml",
            timeout=6,
            headers={"User-Agent": "SeismicSafetyItalia/2.0"}
        )
        if r.status_code != 200 or len(r.content) < 100:
            return pd.DataFrame()
        root = ET.fromstring(r.text)
        rows = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            desc  = (item.findtext("description") or "").strip()
            pub   = (item.findtext("pubDate") or "").strip()
            link  = (item.findtext("link") or "").strip()
            try:
                from email.utils import parsedate_to_datetime as _p2d
                dt_obj = _p2d(pub)
                dt_str = dt_obj.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                dt_str = pub
            mag_m = re.search(r"magnitudo\s+(?:\w+\s*=\s*)?(\d+\.?\d*)", desc, re.I)
            mag   = float(mag_m.group(1)) if mag_m else 0.0
            lat_m = re.search(r"Lat:\s*([\d.]+)", desc)
            lon_m = re.search(r"Lon:\s*([\d.]+)", desc)
            dep_m = re.search(r"Profondità:\s*([\d.]+)", desc)
            lat = float(lat_m.group(1)) if lat_m else None
            lon = float(lon_m.group(1)) if lon_m else None
            dep = float(dep_m.group(1)) if dep_m else 0.0
            if lat and lon:
                rows.append({
                    "time":      dt_str,
                    "magnitude": mag,
                    "depth":     dep,
                    "latitude":  lat,
                    "longitude": lon,
                    "location":  title.replace("\n", " ").strip(),
                    "source":    "GOSSIP-OV",
                })
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=900, show_spinner=False)
def fetch_earthquake_data():
    """
    Dati sismici combinati INGV + USGS + EMSC + GOSSIP-OV — chiamate PARALLELE.
    Priorità: INGV > GOSSIP-OV > USGS > EMSC (deduplicazione su lat/lon/mag/tempo).
    Se tutte falliscono, usa il cache su disco dell'ultimo fetch buono.
    """
    ingv_df  = pd.DataFrame()
    usgs_df  = pd.DataFrame()
    emsc_df  = pd.DataFrame()
    gossip_df = pd.DataFrame()

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_fetch_ingv_raw):   "ingv",
            executor.submit(_fetch_usgs_raw):   "usgs",
            executor.submit(_fetch_emsc_raw):   "emsc",
            executor.submit(_fetch_gossip_raw): "gossip",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if not result.empty:
                    if name == "ingv":
                        ingv_df = result
                    elif name == "usgs":
                        usgs_df = result
                    elif name == "emsc":
                        emsc_df = result
                    else:
                        gossip_df = result
            except Exception:
                pass

    combined = pd.concat([ingv_df, gossip_df, usgs_df, emsc_df], ignore_index=True)
    if not combined.empty:
        combined["datetime"] = pd.to_datetime(combined["time"], errors="coerce")
        combined = combined.dropna(subset=["datetime"])
        combined = combined.sort_values("datetime", ascending=False)
        # Deduplicazione: stesso evento riportato da più agenzie
        # Priorità: INGV > GOSSIP-OV > USGS > EMSC
        _src_order = {"INGV": 0, "GOSSIP-OV": 1, "USGS": 2, "EMSC": 3}
        combined["_src_rank"] = combined["source"].map(lambda s: _src_order.get(s, 9))
        combined["_lat_r"]  = combined["latitude"].round(1)
        combined["_lon_r"]  = combined["longitude"].round(1)
        combined["_mag_r"]  = combined["magnitude"].round(1)
        combined["_ts_r"]   = combined["datetime"].dt.round("60s")
        combined = (combined.sort_values("_src_rank")
                            .drop_duplicates(subset=["_lat_r","_lon_r","_mag_r","_ts_r"])
                            .drop(columns=["_src_rank","_lat_r","_lon_r","_mag_r","_ts_r"])
                            .sort_values("datetime", ascending=False))
        combined["formatted_time"] = combined["datetime"].dt.strftime("%d/%m/%Y %H:%M:%S")
        _save_fallback(combined)
        return combined

    # Tutte fallite — usa cache disco
    fallback_df, loaded = _load_fallback()
    if loaded and not fallback_df.empty:
        if "formatted_time" not in fallback_df.columns:
            fallback_df["formatted_time"] = fallback_df["datetime"].dt.strftime("%d/%m/%Y %H:%M:%S")
        return fallback_df

    return pd.DataFrame()


def filter_area_earthquakes(df, area_name):
    if df is None or df.empty:
        return pd.DataFrame()
    area_bounds = {
        "vesuvio":       {"lat_min": 40.75, "lat_max": 40.90, "lon_min": 14.35, "lon_max": 14.55},
        "campi_flegrei": {"lat_min": 40.78, "lat_max": 40.92, "lon_min": 13.95, "lon_max": 14.22},
        "ischia":        {"lat_min": 40.62, "lat_max": 40.88, "lon_min": 13.75, "lon_max": 14.10}
    }
    if area_name in area_bounds:
        b = area_bounds[area_name]
        return df[
            (df["latitude"] >= b["lat_min"]) & (df["latitude"] <= b["lat_max"]) &
            (df["longitude"] >= b["lon_min"]) & (df["longitude"] <= b["lon_max"])
        ].copy()
    return df


def get_significant_earthquakes(df, min_magnitude=3.0, hours=24):
    if df is None or df.empty:
        return pd.DataFrame()
    recent_time = datetime.now() - timedelta(hours=hours)
    return df[(df["magnitude"] >= min_magnitude) & (df["datetime"] >= recent_time)]


def calculate_earthquake_statistics(df):
    if df is None or df.empty:
        return {"count": 0, "avg_magnitude": 0.0, "max_magnitude": 0.0, "avg_depth": 0.0, "daily_counts": {}}
    df = df.copy()
    df["date"] = df["datetime"].dt.date
    daily_counts = {str(k): v for k, v in df.groupby("date").size().to_dict().items()}
    return {
        "count": len(df),
        "avg_magnitude": round(float(df["magnitude"].mean()), 2),
        "max_magnitude": round(float(df["magnitude"].max()), 2),
        "avg_depth": round(float(df["depth"].mean()), 2),
        "daily_counts": daily_counts
    }


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ingv_news(max_items=5):
    """Ultime notizie INGV da RSS — con fallback multi-URL."""
    news_items = []
    urls_to_try = [
        "https://www.ingv.it/index.php?format=feed&type=rss",
        "https://www.ov.ingv.it/index.php/it/news-ov?format=feed&type=rss",
        "https://www.ov.ingv.it/index.php/it/?format=feed&type=rss",
        "https://www.ingv.it/it/?format=feed&type=rss",
    ]
    headers = {"User-Agent": "SeismicSafetyItalia/2.0",
               "Accept": "application/rss+xml, application/xml, text/xml"}
    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=3, headers=headers, allow_redirects=False)
            if resp.status_code != 200:
                continue
            content = resp.content
            if not content or len(content) < 100:
                continue
            root = ET.fromstring(content)
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item")[:max_items]:
                title_el = item.find("title")
                link_el  = item.find("link")
                date_el  = item.find("pubDate")
                desc_el  = item.find("description")
                if title_el is not None and title_el.text:
                    news_items.append({
                        "title": title_el.text.strip(),
                        "link": (link_el.text or "https://www.ingv.it").strip(),
                        "date": (date_el.text or "")[:16],
                        "description": ((desc_el.text or "").strip())[:200]
                    })
            if news_items:
                break
        except Exception:
            continue
    return news_items


def compute_hourly_distribution(df):
    if df is None or df.empty:
        return {}
    return df.groupby(df["datetime"].dt.hour).size().to_dict()


def compute_depth_distribution(df):
    if df is None or df.empty:
        return {}
    bins = {"0-5 km (superficiali)": 0, "5-15 km": 0, "15-30 km": 0, "30+ km (profondi)": 0}
    for d in df["depth"]:
        if d < 5:
            bins["0-5 km (superficiali)"] += 1
        elif d < 15:
            bins["5-15 km"] += 1
        elif d < 30:
            bins["15-30 km"] += 1
        else:
            bins["30+ km (profondi)"] += 1
    return bins


def compute_magnitude_distribution(df):
    if df is None or df.empty:
        return {}
    bins = {"M < 1.5": 0, "M 1.5-2.5": 0, "M 2.5-3.5": 0, "M 3.5-5.0": 0, "M > 5.0": 0}
    for m in df["magnitude"]:
        if m < 1.5:
            bins["M < 1.5"] += 1
        elif m < 2.5:
            bins["M 1.5-2.5"] += 1
        elif m < 3.5:
            bins["M 2.5-3.5"] += 1
        elif m < 5.0:
            bins["M 3.5-5.0"] += 1
        else:
            bins["M > 5.0"] += 1
    return bins
