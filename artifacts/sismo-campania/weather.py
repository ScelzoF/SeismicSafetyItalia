"""
weather.py
Meteo avanzato con Open-Meteo (gratuito, no API key), geolocalizzazione GPS,
previsioni 7 giorni, grafico temperatura/vento/pioggia.
"""

import streamlit as st
import requests
from datetime import datetime, timedelta
import math
import time
from translations_lib import get_text as _gt

CACHE_TTL = 1800  # 30 minuti

CITTA_CAMPANIA = {
    "Napoli": (40.8518, 14.2681),
    "Torre Annunziata": (40.7505, 14.4463),
    "Pozzuoli": (40.8235, 14.1204),
    "Ercolano": (40.8060, 14.3611),
    "Pompei": (40.7463, 14.4989),
    "Castellammare di Stabia": (40.6944, 14.4739),
    "Torre del Greco": (40.7872, 14.3611),
    "Portici": (40.8143, 14.3405),
    "Salerno": (40.6824, 14.7681),
    "Avellino": (40.9143, 14.7903),
    "Caserta": (41.0732, 14.3319),
    "Benevento": (41.1297, 14.7819),
    "Bacoli": (40.8009, 14.0824),
    "Quarto": (40.8780, 14.1435),
    "Somma Vesuviana": (40.8735, 14.4345),
    "Ottaviano": (40.8496, 14.4798),
    "Sorrento": (40.6263, 14.3763),
    "Amalfi": (40.6340, 14.6027),
    "Ischia": (40.7297, 13.9397),
    "Capri": (40.5527, 14.2229),
}

CITTA_ITALIA = {
    "Roma": (41.9028, 12.4964),
    "Milano": (45.4654, 9.1859),
    "Torino": (45.0703, 7.6869),
    "Venezia": (45.4408, 12.3155),
    "Firenze": (43.7696, 11.2558),
    "Bologna": (44.4949, 11.3426),
    "Bari": (41.1171, 16.8719),
    "Palermo": (38.1157, 13.3615),
    "Catania": (37.5079, 15.0830),
    "Messina": (38.1938, 15.5540),
    "Reggio Calabria": (38.1147, 15.6479),
    "L'Aquila": (42.3498, 13.3995),
    "Catanzaro": (38.9099, 16.5875),
    "Genova": (44.4056, 8.9463),
    "Trieste": (45.6497, 13.7768),
    "Perugia": (43.1107, 12.3908),
    "Ancona": (43.6158, 13.5189),
}

WMO_CODES = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
    45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️", 71: "🌨️", 73: "❄️",
    75: "❄️", 77: "🌨️", 80: "🌦️", 81: "🌧️", 82: "⛈️",
    85: "🌨️", 86: "❄️", 95: "⛈️", 96: "⛈️", 99: "⛈️",
}


def _wmo_desc(code):
    emoji = WMO_CODES.get(code, "🌡️")
    key = f"wmo_{code}"
    desc = _gt(key) if key in ["wmo_0","wmo_1","wmo_2","wmo_3","wmo_45","wmo_48",
        "wmo_51","wmo_53","wmo_55","wmo_61","wmo_63","wmo_65","wmo_71","wmo_73",
        "wmo_75","wmo_77","wmo_80","wmo_81","wmo_82","wmo_85","wmo_86","wmo_95",
        "wmo_96","wmo_99"] else _gt("weather_default_condition")
    return (desc, emoji)


def _wind_direction(deg):
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    return dirs[round(deg / 45) % 8]


def _beaufort(ms):
    if ms < 0.3: return _gt("bf_0")
    if ms < 1.6: return _gt("bf_1")
    if ms < 3.4: return _gt("bf_2")
    if ms < 5.5: return _gt("bf_3")
    if ms < 8.0: return _gt("bf_4")
    if ms < 10.8: return _gt("bf_5")
    if ms < 13.9: return _gt("bf_6")
    return _gt("bf_7")


def fetch_openmeteo(lat, lon):
    """Fetch dati meteo da Open-Meteo API (gratuita, no API key)."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"precipitation,weather_code,wind_speed_10m,wind_direction_10m,"
            f"surface_pressure,cloud_cover,visibility"
            f"&hourly=temperature_2m,precipitation_probability,precipitation,"
            f"wind_speed_10m,weather_code"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"precipitation_sum,precipitation_probability_max,"
            f"wind_speed_10m_max,sunrise,sunset,uv_index_max"
            f"&timezone=Europe%2FRome"
            f"&forecast_days=7"
        )
        r = requests.get(url, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def geocode_city(city_name):
    """Geocode city using Nominatim (gratuito, no key)."""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name},Italy&format=json&limit=1"
        r = requests.get(url, headers={"User-Agent": "SeismicSafety/1.0"}, timeout=8)
        if r.status_code == 200 and r.json():
            result = r.json()[0]
            return float(result["lat"]), float(result["lon"]), result.get("display_name", city_name)
    except Exception:
        pass
    return None


def _render_geolocation_button():
    """Rende bottone GPS con JS che aggiorna i query params."""
    btn_label = _gt('emergency_use_gps')
    privacy_note = _gt('gps_privacy_note')
    geo_html = f"""
    <style>html,body{{background:transparent!important;margin:0;padding:0;overflow:hidden;}}</style>
    <script>
    function getLocation() {{
        var btn = document.getElementById('geoBtn');
        btn.textContent = 'Rilevamento...';
        btn.disabled = true;
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(
                function(pos) {{
                    var lat = pos.coords.latitude.toFixed(5);
                    var lon = pos.coords.longitude.toFixed(5);
                    var acc = Math.round(pos.coords.accuracy);
                    btn.textContent = 'GPS: ' + lat + ', ' + lon + ' (\u00b1' + acc + 'm)';
                    var url = new URL(window.parent.location.href);
                    url.searchParams.set('geo_lat', lat);
                    url.searchParams.set('geo_lon', lon);
                    window.parent.location.href = url.toString();
                }},
                function(err) {{
                    btn.textContent = 'GPS n/a (' + err.message + ')';
                    btn.disabled = false;
                }},
                {{enableHighAccuracy: true, timeout: 10000, maximumAge: 60000}}
            );
        }} else {{
            btn.textContent = 'Geolocation not supported';
            btn.disabled = false;
        }}
    }}
    </script>
    <button id="geoBtn" onclick="getLocation()" style="
        background: linear-gradient(135deg, #1a7fc1, #0d5a91);
        color: white; border: none; padding: 10px 20px;
        border-radius: 8px; font-size: 14px; cursor: pointer;
        font-weight: bold; box-shadow: 0 2px 6px #0005;
        transition: opacity 0.2s;">
        {btn_label}
    </button>
    <p style="font-size: 11px; color: #888; margin-top: 6px;">{privacy_note}</p>
    """
    st.html(f"<div style='height:90px;overflow:hidden;'>{geo_html}</div>", unsafe_allow_javascript=True)


def _render_current_conditions(data, city_name, lat, lon):
    """Render condizioni attuali stilizzate."""
    curr = data.get("current", {})
    temp = curr.get("temperature_2m", 0)
    feels = curr.get("apparent_temperature", 0)
    humidity = curr.get("relative_humidity_2m", 0)
    wind_ms = curr.get("wind_speed_10m", 0)
    wind_dir = curr.get("wind_direction_10m", 0)
    pressure = curr.get("surface_pressure", 0)
    cloud = curr.get("cloud_cover", 0)
    precip = curr.get("precipitation", 0)
    wcode = curr.get("weather_code", 0)
    vis = curr.get("visibility", 10000)

    desc, emoji = _wmo_desc(wcode)
    wind_kmh = wind_ms * 3.6
    beaufort = _beaufort(wind_ms)
    wind_dir_str = _wind_direction(wind_dir)

    # Colore sfondo basato su temperatura
    if temp >= 30:
        bg = "linear-gradient(135deg, #ff6b35, #f7c948)"
        text_c = "#5a1a00"
    elif temp >= 20:
        bg = "linear-gradient(135deg, #2980b9, #6dd5fa)"
        text_c = "#002244"
    elif temp >= 10:
        bg = "linear-gradient(135deg, #4ca1af, #c4e0e5)"
        text_c = "#1a3a4a"
    else:
        bg = "linear-gradient(135deg, #4facfe, #00f2fe)"
        text_c = "#001a2a"

    st.markdown(
        f"""<div style='background:{bg};padding:20px;border-radius:14px;color:{text_c};
                        box-shadow:0 4px 16px #0002;margin-bottom:16px;'>
        <h2 style='margin:0 0 4px 0;font-size:1.6em;'>{emoji} {city_name}</h2>
        <div style='font-size:0.85em;opacity:0.8;margin-bottom:12px;'>
        📍 {lat:.4f}°N, {lon:.4f}°E &nbsp;|&nbsp; Open-Meteo &nbsp;|&nbsp;
        {_gt('weather_update_label') if False else ''}{datetime.now().strftime("%H:%M")}</div>
        <div style='display:flex;gap:30px;flex-wrap:wrap;'>
            <div style='text-align:center;'>
                <div style='font-size:3.2em;font-weight:900;line-height:1.1;'>{temp:.1f}°C</div>
                <div style='font-size:0.9em;'>{_gt('weather_perceived')} {feels:.1f}°C</div>
            </div>
            <div style='font-size:0.95em;line-height:1.9;'>
                <b>{desc}</b><br>
                💧 {_gt('weather_humidity')}: {humidity}%<br>
                🌬️ {_gt('weather_wind')}: {wind_kmh:.0f} km/h {wind_dir_str} ({beaufort})<br>
                🌡️ {_gt('weather_pressure')}: {pressure:.0f} hPa<br>
                ☁️ {_gt('weather_cloud')}: {cloud}%<br>
                🌂 Prec. ora: {precip:.1f} mm
            </div>
            <div style='font-size:0.95em;line-height:1.9;'>
                👁️ {_gt('weather_visibility')}: {vis/1000:.0f} km<br>
                🧭 Dir. vento: {wind_dir:.0f}° ({wind_dir_str})<br>
            </div>
        </div>
        </div>""",
        unsafe_allow_html=True
    )


def _render_forecast_7days(data):
    """Render previsioni 7 giorni con metriche."""
    daily = data.get("daily", {})
    if not daily:
        return

    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    precip_prob = daily.get("precipitation_probability_max", [])
    wind_max = daily.get("wind_speed_10m_max", [])
    sunrises = daily.get("sunrise", [])
    sunsets = daily.get("sunset", [])
    uv = daily.get("uv_index_max", [])

    st.markdown(f"### {_gt('weather_7day_title')}")

    giorni_it = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

    cols = st.columns(min(7, len(dates)))
    for i, (col, date_str) in enumerate(zip(cols, dates)):
        with col:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if i == 0:
                    day_label = "Oggi"
                elif i == 1:
                    day_label = "Domani"
                else:
                    day_label = giorni_it[date_obj.weekday()]
                date_display = date_obj.strftime("%d/%m")
            except Exception:
                day_label = date_str
                date_display = ""

            wcode = codes[i] if i < len(codes) else 0
            desc, emoji = _wmo_desc(wcode)
            tmax = t_max[i] if i < len(t_max) else "--"
            tmin = t_min[i] if i < len(t_min) else "--"
            prec = precip[i] if i < len(precip) else 0
            pprob = precip_prob[i] if i < len(precip_prob) else 0
            wmax = wind_max[i] if i < len(wind_max) else 0
            uv_val = uv[i] if i < len(uv) else 0

            # Colore background card
            if tmax and tmax >= 30:
                card_bg = "#fff3cd"
                border_c = "#ff9800"
            elif prec and prec > 5:
                card_bg = "#e3f2fd"
                border_c = "#2196f3"
            else:
                card_bg = "#f8fff8"
                border_c = "#4caf50"

            st.markdown(
                f"""<div style='background:{card_bg};border:2px solid {border_c};
                    border-radius:10px;padding:10px;text-align:center;font-size:0.85em;
                    min-height:180px;'>
                <b>{day_label}</b><br>
                <span style='font-size:0.8em;color:#666;'>{date_display}</span><br>
                <span style='font-size:2em;'>{emoji}</span><br>
                <b style='color:#e63946;'>{tmax:.0f}°</b> / <span style='color:#457b9d;'>{tmin:.0f}°</span><br>
                <span style='font-size:0.8em;'>
                🌧️ {prec:.1f}mm ({pprob:.0f}%)<br>
                💨 {wmax:.0f}km/h<br>
                ☀️ UV {uv_val:.0f}
                </span></div>""",
                unsafe_allow_html=True
            )

    # Grafico temperatura 7 giorni
    st.markdown("### 📈 Andamento Temperatura 7 Giorni")
    if t_max and t_min:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax1 = plt.subplots(figsize=(12, 4), dpi=110)
        fig.patch.set_facecolor("#0e1117")
        ax1.set_facecolor("#1a1a2e")

        xs = range(len(dates))
        day_labels = []
        for i, d in enumerate(dates):
            try:
                do = datetime.strptime(d, "%Y-%m-%d")
                if i == 0:
                    day_labels.append("Oggi")
                elif i == 1:
                    day_labels.append("Domani")
                else:
                    gi = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
                    day_labels.append(gi[do.weekday()] + "\n" + do.strftime("%d/%m"))
            except Exception:
                day_labels.append(d)

        ax1.fill_between(xs, t_min, t_max, alpha=0.3, color="#4fc3f7", label="Escursione termica")
        ax1.plot(xs, t_max, "o-", color="#ff6b6b", lw=2, ms=7, label="Tmax")
        ax1.plot(xs, t_min, "o-", color="#4fc3f7", lw=2, ms=7, label="Tmin")

        for i, (tma, tmi) in enumerate(zip(t_max, t_min)):
            ax1.annotate(f"{tma:.0f}°", (i, tma), textcoords="offset points",
                         xytext=(0, 8), ha="center", fontsize=9, color="#ff6b6b", fontweight="bold")
            ax1.annotate(f"{tmi:.0f}°", (i, tmi), textcoords="offset points",
                         xytext=(0, -14), ha="center", fontsize=9, color="#4fc3f7")

        ax1.set_xticks(list(xs))
        ax1.set_xticklabels(day_labels, fontsize=9, color="white")
        ax1.tick_params(colors="white", labelsize=9)
        ax1.set_ylabel("°C", color="white", fontsize=10)
        ax1.yaxis.label.set_color("white")
        for spine in ax1.spines.values():
            spine.set_edgecolor("#444")
        ax1.grid(axis="y", color="#333", linestyle="--", alpha=0.5)
        ax1.legend(loc="upper right", fontsize=8, facecolor="#1a1a2e", labelcolor="white")
        ax1.set_title("Temperatura Min/Max — 7 giorni", color="white", fontsize=11, pad=10)

        # Precipitation bars
        if precip:
            ax2 = ax1.twinx()
            ax2.set_facecolor("#1a1a2e")
            bars = ax2.bar(xs, precip, alpha=0.4, color="#29b6f6", width=0.4, label="Pioggia (mm)")
            ax2.set_ylabel("mm pioggia", color="#29b6f6", fontsize=9)
            ax2.tick_params(colors="#29b6f6", labelsize=8)
            for spine in ax2.spines.values():
                spine.set_edgecolor("#444")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()


def _render_hourly_chart(data):
    """Render previsioni orarie 24h."""
    hourly = data.get("hourly", {})
    if not hourly:
        return

    times = hourly.get("time", [])[:24]
    temps = hourly.get("temperature_2m", [])[:24]
    precip_prob = hourly.get("precipitation_probability", [])[:24]
    winds = hourly.get("wind_speed_10m", [])[:24]

    if not times:
        return

    st.markdown("### ⏰ Previsioni Orarie — Prossime 24 Ore")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5), dpi=110, sharex=True)
    fig.patch.set_facecolor("#0e1117")
    for ax in [ax1, ax2]:
        ax.set_facecolor("#1a1a2e")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    hour_labels = [t.split("T")[1][:5] if "T" in t else t for t in times]
    xs = range(len(times))

    # Temperature + wind
    ax1.fill_between(xs, temps, min(temps) - 1, alpha=0.3, color="#ff6b6b")
    ax1.plot(xs, temps, "o-", color="#ff6b6b", lw=2, ms=4)
    ax1.set_ylabel("°C", color="white", fontsize=9)
    ax1.tick_params(colors="white", labelsize=8)
    ax1.grid(axis="y", color="#333", linestyle="--", alpha=0.4)
    ax1.set_title("Temperatura & Probabilità Pioggia — 24h", color="white", fontsize=10, pad=5)

    ax1b = ax1.twinx()
    ax1b.plot(xs, winds, "--", color="#80cbc4", lw=1.5, alpha=0.8, label="Vento km/h")
    ax1b.set_ylabel("km/h", color="#80cbc4", fontsize=8)
    ax1b.tick_params(colors="#80cbc4", labelsize=8)

    # Precipitation probability
    ax2.bar(xs, precip_prob, color="#29b6f6", alpha=0.7, width=0.8)
    ax2.set_ylabel("Prob. pioggia %", color="white", fontsize=9)
    ax2.set_ylim(0, 100)
    ax2.tick_params(colors="white", labelsize=8)
    ax2.grid(axis="y", color="#333", linestyle="--", alpha=0.4)

    # x-axis labels (every 3 hours)
    tick_positions = list(range(0, len(times), 3))
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels([hour_labels[i] for i in tick_positions], rotation=45, fontsize=8, color="white")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def show_meteo():
    """Entry point — sezione meteo completa."""
    st.subheader(_gt("weather_title"))

    # Leggi coordinate GPS dai query params (settati dal JS geolocation)
    params = st.query_params
    geo_lat = params.get("geo_lat")
    geo_lon = params.get("geo_lon")
    has_gps = geo_lat is not None and geo_lon is not None

    # Selezione città
    col_mode, col_city, col_gps = st.columns([2, 3, 2])

    MODE_KEYS = ["campania", "italia", "gps", "search"]
    mode_labels = [_gt("weather_tab_campania"), _gt("weather_tab_italia"), _gt("weather_tab_gps"), _gt("weather_tab_search")]
    with col_mode:
        mode_idx = st.radio(
            _gt("weather_select_position"),
            range(4),
            format_func=lambda i: mode_labels[i],
            horizontal=False,
            key="meteo_mode"
        )
    mode = MODE_KEYS[mode_idx]

    lat, lon, city_name = None, None, "Torre Annunziata"

    with col_city:
        if mode == "campania":
            city_sel = st.selectbox(
                _gt("weather_tab_campania"),
                list(CITTA_CAMPANIA.keys()),
                index=list(CITTA_CAMPANIA.keys()).index("Torre Annunziata"),
                key="meteo_city_camp"
            )
            lat, lon = CITTA_CAMPANIA[city_sel]
            city_name = city_sel

        elif mode == "italia":
            city_sel = st.selectbox(
                _gt("weather_tab_italia"),
                list(CITTA_ITALIA.keys()),
                key="meteo_city_ita"
            )
            lat, lon = CITTA_ITALIA[city_sel]
            city_name = city_sel

        elif mode == "gps":
            if has_gps:
                try:
                    lat = float(geo_lat)
                    lon = float(geo_lon)
                    city_name = f"GPS ({lat:.4f}°N, {lon:.4f}°E)"
                    st.success(f"{_gt('weather_gps_detected')}: {lat:.4f}°N, {lon:.4f}°E")
                except Exception:
                    pass
            else:
                st.info(_gt("gps_hint"))
                lat, lon = CITTA_CAMPANIA["Napoli"]
                city_name = _gt("weather_gps_default")

        elif mode == "search":
            city_input = st.text_input(
                _gt("weather_city_search"),
                value="",
                placeholder=_gt("weather_city_placeholder"),
                key="meteo_city_custom"
            )
            if city_input:
                result = geocode_city(city_input)
                if result:
                    lat, lon, full_name = result
                    city_name = city_input.capitalize()
                    st.success(f"{_gt('weather_city_found')}: {full_name[:60]}")
                else:
                    st.warning(_gt("city_not_found"))
                    lat, lon = CITTA_CAMPANIA["Napoli"]
                    city_name = "Napoli"
            else:
                lat, lon = CITTA_CAMPANIA["Napoli"]
                city_name = "Napoli"

    with col_gps:
        st.markdown("<br>", unsafe_allow_html=True)
        _render_geolocation_button()
        if has_gps:
            if st.button(_gt("weather_gps_remove"), key="remove_gps"):
                st.query_params.clear()
                st.rerun()

    if lat is None or lon is None:
        lat, lon = CITTA_CAMPANIA["Napoli"]
        city_name = "Napoli"

    # Cache key basato su posizione e tempo
    cache_key = f"weather_{lat:.3f}_{lon:.3f}"
    cache_time_key = f"weather_time_{lat:.3f}_{lon:.3f}"

    if cache_key not in st.session_state or cache_time_key not in st.session_state:
        st.session_state[cache_key] = None
        st.session_state[cache_time_key] = 0

    elapsed = time.time() - st.session_state[cache_time_key]

    _wc1, _wc2 = st.columns([5, 1])
    with _wc1:
        if st.session_state[cache_key]:
            remaining = max(0, CACHE_TTL - int(elapsed))
            st.caption(f"{_gt('weather_next_update')} {remaining//60}min {remaining%60}s")
        else:
            st.caption(f"⏳ {_gt('weather_loading')} {city_name}...")
    with _wc2:
        if st.button("🔄", key="meteo_refresh", help=_gt("refresh")):
            st.session_state[cache_key] = None
            st.session_state[cache_time_key] = 0

    if st.session_state[cache_key] is None or elapsed > CACHE_TTL:
        with st.spinner(f"{_gt('weather_loading')} {city_name}..."):
            data = fetch_openmeteo(lat, lon)
            if data:
                st.session_state[cache_key] = data
                st.session_state[cache_time_key] = time.time()
            else:
                st.error(_gt("weather_load_error"))
                return

    data = st.session_state[cache_key]
    if not data:
        return

    # RENDER COMPLETO
    _render_current_conditions(data, city_name, lat, lon)

    tab_7g, tab_24h = st.tabs([_gt("weather_tab_7days"), _gt("weather_tab_24h")])
    with tab_7g:
        _render_forecast_7days(data)
    with tab_24h:
        _render_hourly_chart(data)

    # Alert meteo
    daily = data.get("daily", {})
    t_max_list = daily.get("temperature_2m_max", [])
    precip_list = daily.get("precipitation_sum", [])
    wind_max_list = daily.get("wind_speed_10m_max", [])

    alerts = []
    if t_max_list and max(t_max_list) >= 35:
        alerts.append(f"{_gt('weather_heatwave')}: max prevista {max(t_max_list):.0f}°C")
    if precip_list and max(precip_list) >= 30:
        alerts.append(f"{_gt('weather_flood_risk')}: precipitazioni fino a {max(precip_list):.0f}mm previste")
    if wind_max_list and max(wind_max_list) >= 60:
        alerts.append(f"{_gt('weather_wind_warning')}: raffiche fino a {max(wind_max_list):.0f}km/h")

    if alerts:
        st.markdown("---")
        st.markdown(_gt("weather_alerts_header"))
        for alert in alerts:
            st.warning(alert)

    st.caption(
        "🌐 Dati: [Open-Meteo](https://open-meteo.com) (gratuito, no API key) | "
        "Aggiornamento automatico ogni 30 minuti"
    )
