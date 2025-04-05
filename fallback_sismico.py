
import pandas as pd
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_ingv():
    url = "https://webservices.ingv.it/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": datetime.utcnow().date().isoformat() + "T00:00:00"
    }
    try:
        resp = requests.get(url, params=params, timeout=2)
        resp.raise_for_status()
        data = resp.json().get("features", [])
        events = []
        for q in data:
            props = q.get("properties", {})
            geo = q.get("geometry", {}).get("coordinates", [0, 0, 0])
            events.append({
                "time": props.get("time"),
                "magnitude": props.get("mag", 0),
                "depth": geo[2] if len(geo) > 2 else 0,
                "latitude": geo[1] if len(geo) > 1 else 0,
                "longitude": geo[0] if len(geo) > 0 else 0,
                "location": props.get("place", "Sconosciuto"),
                "source": "INGV"
            })
        return pd.DataFrame(events), "Fonte: INGV"
    except Exception:
        return pd.DataFrame(), None

def fetch_usgs():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": datetime.utcnow().date().isoformat() + "T00:00:00",
        "minmagnitude": 1.0,
        "latitude": 40.85,
        "longitude": 14.25,
        "maxradiuskm": 100,
        "limit": 500
    }
    try:
        resp = requests.get(url, params=params, timeout=2)
        resp.raise_for_status()
        data = resp.json().get("features", [])
        events = []
        for q in data:
            props = q.get("properties", {})
            geo = q.get("geometry", {}).get("coordinates", [0, 0, 0])
            events.append({
                "time": props.get("time"),
                "magnitude": props.get("mag", 0),
                "depth": geo[2] if len(geo) > 2 else 0,
                "latitude": geo[1] if len(geo) > 1 else 0,
                "longitude": geo[0] if len(geo) > 0 else 0,
                "location": props.get("place", "Sconosciuto"),
                "source": "USGS"
            })
        return pd.DataFrame(events), "Fonte temporanea: USGS (INGV non disponibile)"
    except Exception:
        return pd.DataFrame(), None

def get_sismic_data():
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(fetch_ingv): "INGV",
            executor.submit(fetch_usgs): "USGS"
        }
        for future in as_completed(futures):
            df, fonte = future.result()
            if not df.empty:
                return df, fonte
    return pd.DataFrame(), "⚠️ Errore nel recupero dati da INGV e USGS."
