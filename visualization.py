"""
visualization.py
Tutte le visualizzazioni dell'app — dati sismici REALI da INGV/USGS,
dati vulcanologici REALI da INGV OV, GPS reale da Nevada Geodetic Lab,
qualità aria reale da OpenAQ/ARPA Campania.
"""

import warnings
import requests
warnings.filterwarnings("ignore", message=".*components.v1.html.*")
warnings.filterwarnings("ignore", message=".*st.iframe.*")
warnings.filterwarnings("ignore", message=".*width.*stretch.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="streamlit")


_ZONA_IMG = {
    "campania": "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f30b.png",
    "italia":   "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f1ee-1f1f9.png",
    "mondo":    "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f30d.png",
}

def _zona_kind(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return "mondo"
    if 39.9 <= lat <= 41.5 and 13.5 <= lon <= 16.0:
        return "campania"
    if 35.5 <= lat <= 47.1 and 6.6 <= lon <= 18.55:
        return "italia"
    return "mondo"

def _zona_label(lat, lon):
    """Restituisce URL immagine: 🌋 Campania, 🇮🇹 Italia, 🌍 Mondo."""
    return _ZONA_IMG[_zona_kind(lat, lon)]

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static

from data_service import (
    calculate_earthquake_statistics,
    compute_depth_distribution,
    compute_magnitude_distribution,
    compute_hourly_distribution,
    fetch_ingv_news,
    filter_area_earthquakes,
    fetch_earthquake_data_for_ml,
    fetch_earthquake_data_for_ml_area,
)
import data_service
from translations_lib import get_text as _gt
from ml_forecast_service import run_ml_forecast
from ingv_monitor import (
    fetch_gps_rite,
    fetch_gps_vesuvio,
    fetch_gps_ischia,
    fetch_air_quality_campania,
    fetch_air_quality_vesuvio,
    fetch_air_quality_ischia,
    get_ingv_bulletin_values,
    fetch_bulletin_values_live,
    compute_seismic_energy,
    get_seismic_forecast,
    fetch_ingv_alert_level,
    fetch_summit_temperature,
    fetch_gossip_events,
    fetch_gossip_fdsnws,
    fetch_noaa_co2,
    fetch_bulletin_pdf_bytes,
    fetch_storico_confronto,
    _ingv_get,
    GOSSIP_URLS,
    VBKE_SEISMOGRAM_URL,
    ASCH_SEISMOGRAM_URL,
    IOCA_SEISMOGRAM_URL,
    RSAM_URLS,
    GEOCHEM_URLS,
    ZONE_RISCHIO,
    fetch_shakemap_events,
    detect_seismic_swarms,
    get_bradisismo_storico_cf,
    GRANDI_EVENTI_STORICI,
)


def _dm(light_val: str, dark_val: str) -> str:
    """Ritorna dark_val se dark mode attivo, altrimenti light_val."""
    return dark_val if st.session_state.get("dark_mode", False) else light_val

# ─── Palette colori light theme ───────────────────────────────────────────
PALETTE = {
    "primary": "#e63946",
    "secondary": "#457b9d",
    "accent": "#f4a261",
    "bg_card": "#ffffff",
    "text_muted": "#6c757d",
    "low": "#27ae60",
    "medium": "#f39c12",
    "high": "#e63946",
}

DEPTH_COLORS = {
    "0-5 km (superficiali)": "#e63946",
    "5-15 km": "#ff9f43",
    "15-30 km": "#64b5f6",
    "30+ km (profondi)": "#90caf9",
}


def _show_volcano_satellite_map(lat, lon, name, zoom=13, height=340):
    """Mappa satellite ESRI reale con folium — immagine reale via tile WorldImagery."""
    from streamlit_folium import st_folium
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, width="100%", height=height)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri, USGS, NOAA — immagine satellite reale",
        name="Satellite ESRI",
        overlay=False,
        control=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri",
        name="Labels",
        overlay=True,
        control=False,
        opacity=0.7,
    ).add_to(m)
    folium.Circle(
        [lat, lon], radius=5000, color="#ff6b35", fill=True,
        fill_color="#ff6b35", fill_opacity=0.12, tooltip=f"{name} — Raggio 5km"
    ).add_to(m)
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(f"<b>{name}</b><br>Lat: {lat:.4f} N<br>Lon: {lon:.4f} E", max_width=200),
        tooltip=name,
        icon=folium.Icon(color="red", icon="fire", prefix="fa"),
    ).add_to(m)
    st.caption(f"🛰️ Immagine satellite reale — {name} | Fonte: Esri/USGS/NOAA")
    st_folium(m, height=height, returned_objects=[])


def _card(label, value, delta=None, help_text=None):
    st.metric(label=label, value=value, delta=delta, help=help_text)


def _data_freshness_badge(label: str = "INGV/USGS", ttl_min: int = 15):
    """Badge compatto di qualità dato — mostra last_data_fetch dalla session."""
    from datetime import datetime as _dt
    fetch_time = st.session_state.get("last_data_fetch")
    if fetch_time:
        age_s = (_dt.now() - fetch_time).total_seconds()
        if age_s < ttl_min * 60 * 0.5:
            icon, color, stato = "✅", "#27ae60", "live"
        elif age_s < ttl_min * 60:
            icon, color, stato = "⚠️", "#e67e22", "cache"
        else:
            icon, color, stato = "🔄", "#3498db", "aggiornamento…"
        ts = fetch_time.strftime("%d/%m %H:%M")
        st.markdown(
            f"<p style='font-size:0.76rem;color:#999;margin:-4px 0 8px 0;'>"
            f"📡 <b>{label}</b> · {ts} "
            f"<span style='color:{color};font-weight:700;'>{icon} {stato}</span></p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<p style='font-size:0.76rem;color:#bbb;margin:-4px 0 8px 0;'>"
            f"📡 <b>{label}</b> · in caricamento…</p>",
            unsafe_allow_html=True,
        )


def _section_divider(title):
    st.markdown(
        f"<hr style='border:1px solid #dee2e6;margin:14px 0 8px 0;'>"
        f"<h4 style='color:{PALETTE['secondary']};margin-bottom:6px;'>{title}</h4>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# BANNER SCIAME SISMICO — analisi real-time (detect_seismic_swarms)
# ─────────────────────────────────────────────────────────────────────────────

def _show_swarm_banner(df: pd.DataFrame, area_key: str) -> None:
    """
    Mostra un banner di allerta se viene rilevato uno sciame sismico nell'area
    nelle ultime 2 ore (soglia: ≥ 5 eventi nel bounding box vulcanico).
    Non lancia eccezioni — fallisce silenziosamente se il DF non è adatto.
    """
    _AREA_LABEL = {
        "vesuvio":       "Vesuvio",
        "campi_flegrei": "Campi Flegrei",
        "ischia":        "Ischia",
    }
    try:
        swarms = detect_seismic_swarms(df, window_hours=2.0, min_count=5)
        target = _AREA_LABEL.get(area_key, area_key)
        for s in swarms:
            if s["area"] == target:
                _t_start = s["start_time"]
                _t_str = (
                    _t_start.strftime("%H:%M") if hasattr(_t_start, "strftime") else str(_t_start)[:16]
                )
                st.warning(
                    f"🔴 **SCIAME SISMICO IN CORSO — {s['area']}** &nbsp;|&nbsp; "
                    f"**{s['count']} scosse** nelle ultime 2 ore &nbsp;|&nbsp; "
                    f"M max **{s['max_mag']:.1f}** · M min {s['min_mag']:.1f} &nbsp;|&nbsp; "
                    f"Prima scossa: {_t_str} UTC",
                    icon="⚠️",
                )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# MAPPA 3D PROFONDITÀ IPOCENTRALI — Plotly Scatter3d
# ─────────────────────────────────────────────────────────────────────────────

def _show_3d_depth_map(df: pd.DataFrame, area_name: str, plot_key: str) -> None:
    """
    Visualizzazione 3D degli ipocentrici: longitudine × latitudine × profondità.
    I punti sono colorati per magnitudo e dimensionati in proporzione.
    """
    _needed = {"latitude", "longitude", "depth", "magnitude"}
    if df is None or df.empty or not _needed.issubset(df.columns):
        return

    _data = df.dropna(subset=["latitude", "longitude", "depth", "magnitude"]).copy()
    if _data.empty:
        return

    with st.expander(f"🌐 Mappa 3D Profondità Ipocentrali — {area_name}", expanded=False):
        _sizes = np.clip(_data["magnitude"].values * 2.8 + 2, 3, 16).tolist()
        _hover = [
            f"M{row['magnitude']:.1f} · Prof. {row['depth']:.1f} km<br>{row.get('location', '')}"
            for _, row in _data.iterrows()
        ]
        fig = go.Figure(data=[go.Scatter3d(
            x=_data["longitude"].tolist(),
            y=_data["latitude"].tolist(),
            z=(-_data["depth"]).tolist(),
            mode="markers",
            marker=dict(
                size=_sizes,
                color=_data["magnitude"].tolist(),
                colorscale="Reds",
                cmin=float(_data["magnitude"].min()),
                cmax=float(_data["magnitude"].max()),
                opacity=0.78,
                colorbar=dict(title="Mag", thickness=10, len=0.6),
                showscale=True,
            ),
            text=_hover,
            hovertemplate="%{text}<extra></extra>",
        )])
        fig.update_layout(
            scene=dict(
                xaxis=dict(title="Longitudine", backgroundcolor="rgba(0,0,0,0)", gridcolor="#555"),
                yaxis=dict(title="Latitudine",  backgroundcolor="rgba(0,0,0,0)", gridcolor="#555"),
                zaxis=dict(title="Profondità km (↓)", backgroundcolor="rgba(0,0,0,0)", gridcolor="#555"),
                bgcolor="rgba(0,0,0,0)",
                aspectmode="manual",
                aspectratio=dict(x=1.5, y=1.5, z=0.6),
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=480,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        )
        st.plotly_chart(fig, width="stretch", key=plot_key)
        st.caption(
            f"🌐 {len(_data)} ipocentrici · Asse Z = profondità negativa (in basso) · "
            "Rotazione con mouse · Zoom con scroll · Hover per dettagli"
        )


# ─────────────────────────────────────────────────────────────────────────────
# STORICO BRADISISMO CAMPI FLEGREI — Grafico multi-decennale (INGV OV)
# ─────────────────────────────────────────────────────────────────────────────

def _render_bradisismo_storico_cf(gps_data: dict | None = None) -> None:
    """
    Grafico interattivo del sollevamento cumulativo ai Campi Flegrei (1950→oggi).
    Due tracce: crisi storiche (1950-2005) + ciclo attuale GPS RITE (2005→oggi).
    Se gps_data è fornito aggiunge il tasso attuale come annotazione.
    """
    df_brd = get_bradisismo_storico_cf()
    _storica = df_brd[df_brd["serie"] == "storica"].sort_values("year")
    _recente = df_brd[df_brd["serie"] == "recente"].sort_values("year")

    fig = go.Figure()

    # Traccia storica
    fig.add_trace(go.Scatter(
        x=_storica["year"].tolist(),
        y=_storica["uplift_mm"].tolist(),
        mode="lines+markers",
        name="Crisi storiche (1950–2005)",
        line=dict(color="#e74c3c", width=2.5, dash="solid"),
        marker=dict(size=7, symbol="circle"),
        text=_storica["note"].tolist(),
        hovertemplate="Anno %{x:.0f}<br>Sollevamento: <b>%{y} mm</b><br>%{text}<extra></extra>",
    ))
    # Picco 1984 — annotazione critica
    fig.add_annotation(
        x=1984.5, y=3450,
        text="Picco 2ª crisi<br>+3.45 m (1984)",
        showarrow=True, arrowhead=2, arrowcolor="#e74c3c",
        font=dict(size=10, color="#e74c3c"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#e74c3c", borderwidth=1,
        ax=60, ay=-40,
    )

    # Traccia ciclo attuale (asse Y secondario, riferimento 2005=0)
    fig.add_trace(go.Scatter(
        x=_recente["year"].tolist(),
        y=_recente["uplift_mm"].tolist(),
        mode="lines+markers",
        name="Ciclo attuale GPS RITE (2005=0)",
        line=dict(color="#f39c12", width=2.5, dash="solid"),
        marker=dict(size=7, symbol="diamond"),
        text=_recente["note"].tolist(),
        yaxis="y2",
        hovertemplate="Anno %{x:.1f}<br>Sollevamento RITE: <b>%{y} mm</b><br>%{text}<extra></extra>",
    ))

    # Tasso attuale live da GPS
    if gps_data and gps_data.get("monthly_rate_mm") is not None:
        _rate = gps_data["monthly_rate_mm"]
        _station = gps_data.get("station", "RITE")
        _src_icon = "🟢 LIVE" if gps_data.get("source_type") == "live" else "📡"
        fig.add_annotation(
            x=2026.1, y=_recente["uplift_mm"].iloc[-1],
            text=f"{_src_icon} {_station}<br>{_rate:+.1f} mm/mese",
            showarrow=True, arrowhead=2, arrowcolor="#f39c12",
            font=dict(size=10, color="#f39c12"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#f39c12", borderwidth=1,
            ax=-70, ay=-30,
            yref="y2",
        )

    # Zona "allerta livello storico"
    fig.add_hrect(
        y0=3200, y1=3500,
        fillcolor="rgba(231,76,60,0.08)",
        line_width=0,
        annotation_text="Zona picco 1984",
        annotation_position="top left",
        annotation_font_size=9,
        annotation_font_color="#e74c3c",
    )

    fig.update_layout(
        title=dict(
            text="📉 Sollevamento/Subsidenza Storica — Campi Flegrei (Rione Terra / GPS RITE)",
            font_size=13,
        ),
        xaxis=dict(title="Anno", dtick=10, gridcolor="#eee"),
        yaxis=dict(
            title="Sollevamento cumulativo mm<br>(rif. 1950)",
            gridcolor="#eee",
        ),
        yaxis2=dict(
            title="Sollevamento mm<br>(rif. 2005 = 0)",
            overlaying="y",
            side="right",
            showgrid=False,
            color="#f39c12",
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.7)", font_size=11),
        hovermode="x unified",
        height=400,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,249,250,0.6)",
    )
    st.plotly_chart(fig, width="stretch", key="bradisismo_storico_cf")
    st.caption(
        "📚 Fonti: INGV OV Bollettini storici · Barberi et al. (1984) · Chiodini et al. (2017) · "
        "GPS RITE da bollettini INGV OV (rete RING — non su NGL). I valori 1950–2005 sono espressi "
        "rispetto al benchmark Rione Terra; il ciclo attuale (arancio) è relativo al riferimento GPS RITE 2005=0."
    )


# ─────────────────────────────────────────────────────────────────────────────
# GRANDI EVENTI STORICI — Pannello confronto contestuale per area
# ─────────────────────────────────────────────────────────────────────────────

def _render_grandi_eventi_storici(area_key: str) -> None:
    """
    Mostra una scheda contestuale con i principali eventi storici dell'area
    (eruzioni, terremoti, crisi bradisismiche) per dare contesto all'attività attuale.
    """
    _FILTER_MAP = {
        "vesuvio":       ["Vesuvio", "Campania"],
        "campi_flegrei": ["Campi Flegrei", "Campania"],
        "ischia":        ["Ischia", "Campania"],
        "all":           None,
    }
    _area_filter = _FILTER_MAP.get(area_key)
    _events = [
        e for e in GRANDI_EVENTI_STORICI
        if _area_filter is None or e["area"] in _area_filter
    ]
    if not _events:
        return

    _TYPE_COLOR = {
        "🌋 Eruzione":   ("#fff3e0", "#f39c12", "#7d5b00"),
        "⚡ Terremoto":  ("#fdecea", "#e74c3c", "#7d1a12"),
        "🏔️ Bradisismo": ("#e8f5e9", "#27ae60", "#155724"),
    }

    with st.expander("📜 Contesto Storico — Grandi eventi dell'area", expanded=False):
        st.markdown(
            "<small style='color:#888;'>Principali eventi storici per contestualizzare "
            "l'attività in corso. Fonti ufficiali INGV, letteratura scientifica peer-reviewed.</small>",
            unsafe_allow_html=True,
        )
        for ev in sorted(_events, key=lambda e: e["anno"], reverse=True):
            _tipo  = ev["tipo"]
            _bg, _border, _txt = _TYPE_COLOR.get(_tipo, ("#f8f9fa", "#6c757d", "#333"))
            _mag_str = f" · M**{ev['mag']}**" if ev["mag"] else ""
            _vit_str = f" · {ev['vittime']:,} vittime" if ev.get("vittime") else ""
            st.markdown(
                f"<div style='background:{_bg};border-left:4px solid {_border};"
                f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                f"<div style='font-size:12px;color:{_txt};font-weight:700;margin-bottom:2px;'>"
                f"{_tipo} &nbsp;·&nbsp; {ev['mese']} {ev['anno']}</div>"
                f"<div style='font-size:14px;font-weight:700;color:{_txt};'>{ev['titolo']}"
                f"{_mag_str}</div>"
                f"<div style='font-size:12px;color:#444;margin-top:4px;'>{ev['desc']}"
                f"{_vit_str}</div>"
                f"<div style='font-size:10px;color:#888;margin-top:4px;'>📚 {ev['fonte']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════
# PAGINA MONITORAGGIO PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════

def show_monitoring_page(earthquake_data, get_text):
    st.header("📊 " + get_text("monitoring"))

    if earthquake_data is None or earthquake_data.empty:
        st.warning("⚠️ " + get_text("no_data"))
        st.info(_gt("data_auto_update"))
        return

    # ── Pre-fetch PARALLELO di tutti i dati pesanti prima dei tab ──────────
    # Riscalda la cache in una sola finestra così ogni tab è istantaneo
    if not st.session_state.get("_cache_warmed"):
        from concurrent.futures import ThreadPoolExecutor
        _all_fetches = [
            fetch_bulletin_values_live,
            fetch_ingv_alert_level,
            fetch_gps_rite,
            fetch_gps_vesuvio,
            fetch_air_quality_campania,
            fetch_air_quality_vesuvio,
            fetch_air_quality_ischia,
            fetch_gossip_events,
            fetch_noaa_co2,
        ]
        def _warm(fn):
            try:
                fn()
            except Exception:
                pass
        with st.spinner("⏳ Caricamento dati live…"):
            with ThreadPoolExecutor(max_workers=len(_all_fetches)) as ex:
                futs = [ex.submit(_warm, fn) for fn in _all_fetches]
                # Aspetta max 5s — chi finisce prima popola la cache
                from concurrent.futures import wait as _wait
                _wait(futs, timeout=5)
        st.session_state["_cache_warmed"] = True

    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] button:nth-of-type(1) [data-testid="stMarkdownContainer"] p::before {
            content: "";
            display: inline-block;
            width: 22px;
            height: 15px;
            margin-right: 8px;
            vertical-align: middle;
            background-image: url("https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f1ee-1f1f9.png");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
        }
        </style>
    """, unsafe_allow_html=True)
    _italia_label = _gt("tab_italia").replace("🌍", "").strip()
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        _italia_label,
        _gt("tab_vesuvio"),
        _gt("tab_flegrei"),
        "🏝️ Ischia",
        _gt("tab_data_table"),
    ])

    with tab1:
        try:
            _show_italia_tab(earthquake_data, get_text)
        except Exception as _e:
            st.error(f"Errore tab Italia: {_e}")

    with tab2:
        try:
            _show_vesuvio_tab(earthquake_data, get_text)
        except Exception as _e:
            st.error(f"Errore tab Vesuvio: {_e}")

    with tab3:
        try:
            _show_flegrei_tab(earthquake_data, get_text)
        except Exception as _e:
            st.error(f"Errore tab Campi Flegrei: {_e}")

    with tab4:
        try:
            _show_ischia_tab(earthquake_data, get_text)
        except Exception as _e:
            st.error(f"Errore tab Ischia: {_e}")

    with tab5:
        show_earthquake_table(earthquake_data, get_text)


# ═══════════════════════════════════════════════════════════════════════════
# TAB ITALIA
# ═══════════════════════════════════════════════════════════════════════════

def _show_gossip_widget(area: str):
    """
    Mostra gli eventi sismici degli ultimi 7 giorni via INGV FDSNWS
    (stesso database di GOSSIP OV, risposta testo — circa 2-10 kB).
    RSS GOSSIP come fallback per il singolo evento più recente.
    """
    # Coordinate e raggio per ogni area
    _AREA_GEO = {
        "campi_flegrei": (40.83, 14.14, 10),
        "vesuvio":       (40.821, 14.426, 10),
        "ischia":        (40.748, 13.897, 10),
    }
    lat, lon, radius = _AREA_GEO.get(area, (40.83, 14.14, 10))
    gossip_url = GOSSIP_URLS.get(area, "https://terremoti.ov.ingv.it/gossip/")

    try:
        events = fetch_gossip_fdsnws(area, lat, lon, radius_km=radius, days=7)
        if events:
            ev0 = events[0]
            mag_str = f"M {ev0['magnitude']:.1f}"
            dep_str = f"{ev0['depth']:.1f} km"
            n_7d = len(events)
            st.markdown(
                f"<div style='background:#e8f4f8;border-left:4px solid #0077b6;"
                f"border-radius:6px;padding:8px 12px;font-size:13px;margin-bottom:4px'>"
                f"📡 <b>GOSSIP INGV OV</b> — Ultimo evento: <b>{mag_str}</b> · "
                f"Prof. {dep_str} · {ev0['time']} UTC · "
                f"<b>{n_7d} eventi</b> negli ultimi 7 giorni"
                f" — <a href='{gossip_url}' target='_blank'>Catalogo live →</a>"
                f"</div>",
                unsafe_allow_html=True,
            )
            # Tabella eventi ultimi 7 giorni (max 15 righe)
            with st.expander(f"📋 Ultimi 7 giorni — {n_7d} eventi (INGV FDSNWS / GOSSIP)", expanded=False):
                rows = []
                for e in events[:20]:
                    _lat = e.get("latitude") or e.get("lat", lat)
                    _lon = e.get("longitude") or e.get("lon", lon)
                    rows.append({
                        "Zona":        _zona_label(_lat, _lon),
                        "Data UTC":    e["time"],
                        "Mag":         f"{e['magnitude']:.1f} {e.get('mag_type','')}",
                        "Prof. (km)":  f"{e['depth']:.1f}",
                        "Localizzazione": e["location"],
                    })
                df_ev = pd.DataFrame(rows)
                st.dataframe(df_ev, width="stretch", hide_index=True,
                             column_config={
                                 "Zona": st.column_config.ImageColumn("Zona", width="small"),
                                 "Data UTC": st.column_config.TextColumn(width="medium"),
                                 "Mag": st.column_config.TextColumn(width="small"),
                             })
                st.caption(
                    f"Fonte: INGV FDSNWS (stesso DB GOSSIP OV) · "
                    f"[Catalogo completo →]({gossip_url})"
                )
        else:
            # Fallback: RSS GOSSIP per singolo evento
            rss = fetch_gossip_events()
            rss_area = [e for e in rss if e.get("area") == area] or rss
            if rss_area:
                ev = rss_area[0]
                mag_str = f"M {ev['magnitude']:.1f}" if ev['magnitude'] else "M n.d."
                dep_str = f"{ev['depth']:.1f} km" if ev.get('depth') else "—"
                st.markdown(
                    f"<div style='background:#e8f4f8;border-left:4px solid #0077b6;"
                    f"border-radius:6px;padding:8px 12px;font-size:13px;margin-bottom:6px'>"
                    f"📡 <b>GOSSIP INGV OV</b> — Ultimo evento: <b>{mag_str}</b> · "
                    f"Prof. {dep_str} · {ev.get('label',ev.get('time',''))}"
                    f" — <a href='{gossip_url}' target='_blank'>Catalogo live →</a>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:#f0f0f0;border-left:4px solid #888;"
                    f"border-radius:6px;padding:8px 12px;font-size:13px;margin-bottom:6px'>"
                    f"📡 <b>GOSSIP INGV OV</b> — Nessun evento recente "
                    f"— <a href='{gossip_url}' target='_blank'>Catalogo live →</a></div>",
                    unsafe_allow_html=True,
                )
    except Exception:
        pass


def _render_seismogram_widget(area: str) -> None:
    """
    Widget sismogramma completo.
    Stazioni verificate attive su portale2.ov.ingv.it (aprile 2026):
      Vesuvio : VBKE ✅  OVO ✅
      CF      : OVO ✅  (ASCH/BGNG/CUMA dismesse)
      Ischia  : nessuna stazione attiva su portale2 → link INGV OV
    """
    # Ischia — nessuna stazione disponibile su portale2 → mostra link ufficiale
    if area == "ischia":
        st.markdown("#### 🔊 Sismogramma — INGV OV Ischia")
        _s_bg  = _dm("rgba(30,60,90,0.08)",  "rgba(30,60,90,0.35)")
        _s_brd = _dm("#1e3c5a", "#4a90d9")
        _s_txt = _dm("#1e3c5a", "#a8d0f0")
        _s_lnk = _dm("#1565c0", "#64b5f6")
        st.markdown(
            f"<div style='background:{_s_bg};border:1px solid {_s_brd};"
            f"border-radius:10px;padding:14px 18px;margin:6px 0 10px 0;'>"
            f"<p style='margin:0 0 6px 0;font-size:13px;font-weight:700;color:{_s_txt};'>"
            f"📡 Rete sismica Ischia — INGV OV</p>"
            f"<p style='margin:0 0 10px 0;font-size:12px;color:{_s_txt};opacity:0.85;'>"
            f"I sismogrammi live delle stazioni di Ischia (IOCA, IALD ecc.) non sono "
            f"al momento disponibili su portale2.ov.ingv.it. "
            f"Consulta la pagina ufficiale di monitoraggio INGV OV per i dati aggiornati.</p>"
            f"<a href='https://www.ov.ingv.it/index.php/ischia-stato-attuale' target='_blank' "
            f"style='background:{_s_lnk};color:#fff;text-decoration:none;"
            f"padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;'>"
            f"🔊 Monitoraggio Ischia INGV OV ↗</a>"
            f"&nbsp;&nbsp;"
            f"<a href='https://terremoti.ingv.it/?starttime=now-7d&lat=40.73&lon=13.90&maxradiuskm=20' "
            f"target='_blank' "
            f"style='background:{_s_brd};color:#fff;text-decoration:none;"
            f"padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;'>"
            f"🗺️ Sismicità recente ↗</a>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    # Stazioni verificate attive aprile 2026
    _STATIONS = {
        "vesuvio": [
            ("VBKE", "VBKE — Sommitale"),
            ("OVO",  "OVO — Osservatorio"),
        ],
        "campi_flegrei": [
            ("OVO",  "OVO — Oss. Vesuviano"),
        ],
    }
    _COMPS = {
        "↕ EHZ — Verticale": "EHZ",
        "↑ EHN — Nord":      "EHN",
        "→ EHE — Est":       "EHE",
    }

    stations = _STATIONS.get(area, [("VBKE", "VBKE")])
    sk = area

    st.markdown("#### 🔊 Sismogramma live — INGV OV")
    if len(stations) > 1:
        c1, c2 = st.columns(2)
        with c1:
            labels = [s[1] for s in stations]
            sel_lbl = st.selectbox("📡 Stazione", labels, key=f"sismo_st_{sk}")
            sel_station = next(s[0] for s in stations if s[1] == sel_lbl)
        with c2:
            sel_comp_lbl = st.selectbox("🔧 Componente", list(_COMPS.keys()), key=f"sismo_cp_{sk}")
            sel_comp = _COMPS[sel_comp_lbl]
    else:
        sel_station = stations[0][0]
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"📡 Stazione: **{stations[0][1]}**")
        with c2:
            sel_comp_lbl = st.selectbox("🔧 Componente", list(_COMPS.keys()), key=f"sismo_cp_{sk}")
            sel_comp = _COMPS[sel_comp_lbl]

    url = f"https://portale2.ov.ingv.it/segnali/{sel_station}_{sel_comp}_attuale.html"

    _s_bg  = _dm("rgba(30,60,90,0.08)",  "rgba(30,60,90,0.35)")
    _s_brd = _dm("#1e3c5a", "#4a90d9")
    _s_txt = _dm("#1e3c5a", "#a8d0f0")
    _s_lnk = _dm("#1565c0", "#64b5f6")

    # Per CF aggiungi nota che OVO è la stazione più vicina disponibile
    if area == "campi_flegrei":
        st.caption("ℹ️ Le stazioni CF dedicate (ASCH, BGNG) non sono al momento disponibili su portale2. "
                   "Viene mostrata la stazione OVO (Osservatorio Vesuviano), la più vicina attiva.")

    st.markdown(
        f"<div style='background:{_s_bg};border:1px solid {_s_brd};"
        f"border-radius:10px;padding:14px 18px;margin:6px 0 10px 0;"
        f"display:flex;align-items:center;justify-content:space-between;'>"
        f"<div>"
        f"<p style='margin:0 0 4px 0;font-size:13px;font-weight:700;color:{_s_txt};'>"
        f"📡 {sel_station} · {sel_comp} · Attuale</p>"
        f"<p style='margin:0;font-size:11px;color:{_s_txt};opacity:0.75;'>"
        f"Sismogramma live INGV OV — si apre in nuova scheda</p>"
        f"</div>"
        f"<a href='{url}' target='_blank' "
        f"style='background:{_s_lnk};color:#fff;text-decoration:none;"
        f"padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;"
        f"white-space:nowrap;'>"
        f"🔊 Apri ↗</a>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if st.button("🔄 Aggiorna link", key=f"sismo_ref_{sk}", help="Aggiorna URL sismogramma"):
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# RSAM TREMORE VULCANICO
# ─────────────────────────────────────────────────────────────────────────────

def _render_rsam_widget(area: str) -> None:
    """Tremore vulcanico (RSAM) — portale INGV OV."""
    _RSAM_IMAGES = {
        "vesuvio":       [
            ("VBKEBB_EHZ", "VBKE — Sommitale (EHZ)"),
            ("BKEBB_EHZ",  "BKE — Versante Est (EHZ)"),
        ],
        "campi_flegrei": [
            ("ASCHBB_EHZ", "ASCH — Astroni (EHZ)"),
            ("BGNGBB_EHZ", "BGNG — Bagnoli (EHZ)"),
        ],
        "ischia": [
            ("IOCABB_EHZ", "IOCA — Ischia (EHZ)"),
        ],
    }

    _PERIODS = {
        "Ultime 24h":   "1d",
        "Ultimi 7 gg":  "7d",
        "Ultimi 30 gg": "30d",
    }

    imgs = _RSAM_IMAGES.get(area, _RSAM_IMAGES["vesuvio"])
    st.markdown("#### 📈 Tremore vulcanico (RSAM) — INGV OV")

    col1, col2 = st.columns(2)
    with col1:
        labels = [i[1] for i in imgs]
        sel_lbl = st.selectbox("📡 Stazione", labels, key=f"rsam_st_{area}")
        sel_code = next(i[0] for i in imgs if i[1] == sel_lbl)
    with col2:
        sel_per_lbl = st.selectbox("⏱️ Periodo", list(_PERIODS.keys()), key=f"rsam_per_{area}")
        sel_per = _PERIODS[sel_per_lbl]

    img_url = (
        f"https://portale2.ov.ingv.it/rsam/{sel_code}_RSAM_{sel_per}.png"
    )
    page_url = RSAM_URLS.get(area, "https://portale2.ov.ingv.it/rsam/")

    try:
        resp = _ingv_get(img_url, timeout=5,
                         headers={"User-Agent": "SeismicSafetyItalia/2.0"})
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            st.image(resp.content, width='stretch',
                     caption=f"RSAM {sel_lbl} — {sel_per_lbl} | INGV OV portale2")
        else:
            raise ValueError("no image")
    except Exception:
        st.info(
            f"📊 Il grafico RSAM di **{sel_lbl}** è disponibile direttamente sul portale INGV OV.\n\n"
            f"[🔗 Apri RSAM portale INGV OV ↗]({page_url})"
        )
    st.caption(
        f"Tremore sismico (ampiezza media RMS) — stazione {sel_code} | "
        f"[Portale INGV OV]({page_url})"
    )


# ─────────────────────────────────────────────────────────────────────────────
# GEOCHEMICAL: CO₂ / SO₂ Solfatara — Campi Flegrei
# ─────────────────────────────────────────────────────────────────────────────

def _render_geochem_widget(area: str, aq_data: dict = None, noaa_co2: dict = None) -> None:
    """Monitoraggio geochimico: CO₂, SO₂, flusso Solfatara."""
    _GEOCHEM_PAGE = GEOCHEM_URLS.get(area, "https://www.ov.ingv.it/ov/it/monitoraggio-geochimico.html")

    _gc_bg    = _dm("rgba(69,123,157,0.12)", "rgba(69,123,157,0.22)")
    _gc_brd   = _dm("#457b9d", "#64b5f6")
    _gc_note  = _dm("#555", "#9ab8cc")
    _gc_link  = _dm("#457b9d", "#64b5f6")

    st.markdown(f"#### 🧪 {_gt('geochem_expander').replace('🧪 ', '')}")

    cols = st.columns(3)
    with cols[0]:
        so2_val = "—"
        so2_src = ""
        if aq_data and "so2" in aq_data:
            so2 = aq_data["so2"]
            so2_val = f"{so2.get('value', 0):.1f} {so2.get('unit','µg/m³')}"
            so2_src = so2.get("source", "")
        st.metric(_gt("geochem_so2"), so2_val,
                  help=f"Biossido di zolfo in atmosfera — {so2_src}")

    with cols[1]:
        co2_val = "—"
        co2_src = ""
        if noaa_co2 and noaa_co2.get("co2_ppm"):
            co2_val = f"{noaa_co2['co2_ppm']:.1f} ppm"
            co2_src = f"NOAA Mauna Loa — {noaa_co2.get('date','')}"
        st.metric(_gt("geochem_co2"), co2_val,
                  help=f"CO₂ atmosferico globale — {co2_src}")

    with cols[2]:
        lbl = _gt("geochem_flux") if area == "campi_flegrei" else _gt("geochem_emissions")
        st.metric(lbl, "→ INGV OV",
                  help="Dati emissioni vulcaniche — portale INGV OV")

    st.markdown(
        f"<div style='background:{_gc_bg};border:1px solid {_gc_brd};"
        f"border-radius:8px;padding:10px 14px;margin-top:6px;'>"
        f"<p style='font-size:12px;margin:0 0 6px 0;font-weight:600;'>"
        f"📊 {_gt('geochem_monitoraggio_completo')}</p>"
        f"<p style='font-size:11px;margin:0 0 6px 0;color:{_gc_note};'>"
        f"{_gt('geochem_nota')}</p>"
        f"<a href='{_GEOCHEM_PAGE}' target='_blank' "
        f"style='font-size:12px;font-weight:700;color:{_gc_link};'>"
        f"{_gt('geochem_apri_link')}</a>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ZONE DI RISCHIO — Protezione Civile
# ─────────────────────────────────────────────────────────────────────────────

def _render_zone_rischio(area: str) -> None:
    """Mappa zone di rischio (zona rossa / gialla) Protezione Civile."""
    info = ZONE_RISCHIO.get(area, {})
    if not info:
        return

    _NOME = {"vesuvio": "Vesuvio", "campi_flegrei": "Campi Flegrei", "ischia": "Ischia"}
    nome = _NOME.get(area, area.capitalize())

    _rossa_bg   = _dm("rgba(192,57,43,0.15)", "rgba(192,57,43,0.28)")
    _rossa_txt  = _dm("#c0392b", "#ff8a7a")
    _muted      = _dm("#666",    "#9ab8cc")
    _card2_bg   = _dm("rgba(52,73,94,0.1)",  "rgba(52,73,94,0.3)")
    _card2_brd  = _dm("#7f8c8d", "#3d5472")
    _note_col   = _dm("#555",    "#9ab8cc")
    _link_blue  = _dm("#457b9d", "#64b5f6")

    st.markdown(f"#### 🗺️ {_gt('zone_rischio_expander').replace('🗺️ ', '')}")

    cola, colb = st.columns(2)
    with cola:
        st.markdown(
            f"<div style='background:{_rossa_bg};border:2px solid #ff6b6b;"
            f"border-radius:10px;padding:14px 16px;text-align:center;'>"
            f"<p style='font-size:13px;font-weight:800;color:{_rossa_txt};margin:0 0 4px 0;'>"
            f"{_gt('zona_rossa_card')}</p>"
            f"<p style='font-size:22px;font-weight:900;margin:0;'>{info['comuni']}</p>"
            f"<p style='font-size:12px;color:{_muted};margin:0;'>{_gt('comuni_interessati')}</p>"
            f"<p style='font-size:16px;font-weight:700;margin:4px 0 0 0;'>{info['abitanti']}</p>"
            f"<p style='font-size:11px;color:{_muted};margin:0;'>{_gt('abitanti_rischio')}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with colb:
        mappa_url = info.get("mappa_url", "")
        st.markdown(
            f"<div style='background:{_card2_bg};border:1px solid {_card2_brd};"
            f"border-radius:10px;padding:14px 16px;'>"
            f"<p style='font-size:12px;font-weight:700;margin:0 0 6px 0;'>{_gt('piano_naz_label')}</p>"
            f"<p style='font-size:11px;color:{_note_col};margin:0 0 8px 0;'>{info['note']}</p>"
            f"<a href='{info['piano_url']}' target='_blank' "
            f"style='font-size:11px;font-weight:700;color:#e63946;display:block;margin-bottom:4px;'>"
            f"{_gt('piano_evac_link')}</a>"
            + (f"<a href='{mappa_url}' target='_blank' "
               f"style='font-size:11px;color:{_link_blue};display:block;margin-bottom:4px;'>"
               f"🗺️ Mappa interattiva DPC ↗</a>" if mappa_url else "")
            + f"<a href='{info['dpc_url']}' target='_blank' "
            f"style='font-size:11px;color:{_link_blue};'>"
            f"🛡️ Protezione Civile — {nome} ↗</a>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Mappa folium con zona approssimativa
    try:
        from streamlit_folium import st_folium
        _COORDS = {
            "vesuvio":       (40.821, 14.426, 8, "Vesuvio — Zona Rossa"),
            "campi_flegrei": (40.827, 14.139, 9, "Campi Flegrei — Zona Rossa"),
            "ischia":        (40.730, 13.897, 11, "Ischia — Zona Rossa"),
        }
        lat, lon, zoom, title = _COORDS.get(area, (40.8, 14.2, 9, nome))
        m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, width="100%", height=260)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="© Esri", name="Satellite", overlay=False, control=False,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="© Esri", overlay=True, control=False,
        ).add_to(m)
        # Marker centrale del vulcano
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b>{title}</b><br>{info['comuni']} comuni — {info['abitanti']} ab.", max_width=220),
            tooltip=f"🌋 {nome}",
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
        ).add_to(m)
        # Cerchio zona rossa approssimativa (raggio in km)
        _RADII = {"vesuvio": 8500, "campi_flegrei": 9000, "ischia": 5000}
        folium.Circle(
            [lat, lon],
            radius=_RADII.get(area, 7000),
            color="#e63946", fill=True, fill_opacity=0.15,
            tooltip="Zona Rossa indicativa (DPC)",
        ).add_to(m)
        st_folium(m, width="100%", height=260, returned_objects=[], key=f"zone_{area}")
    except Exception:
        st.caption("Mappa non disponibile — apri il link DPC per la cartografia ufficiale.")


# ─────────────────────────────────────────────────────────────────────────────
# CONFRONTO STORICO — sismicità mese corrente vs anno precedente
# ─────────────────────────────────────────────────────────────────────────────

def _render_confronto_storico(area: str) -> None:
    """Confronto sismicità: mese corrente vs stesso periodo anno precedente."""
    _NOMI = {"vesuvio": "Vesuvio", "campi_flegrei": "Campi Flegrei", "ischia": "Ischia"}
    nome = _NOMI.get(area, area.capitalize())

    st.markdown(f"#### 📊 {_gt('storico_expander').replace('📊 ', '')}")

    with st.spinner(_gt("storico_loading")):
        data = fetch_storico_confronto(area)

    if not data:
        st.warning(_gt("storico_no_data"))
        return

    now_year  = datetime.now().year
    prev_year = now_year - 1
    cur  = data.get(now_year,  {"count": 0, "max_mag": 0.0, "period": "—"})
    prev = data.get(prev_year, {"count": 0, "max_mag": 0.0, "period": "—"})

    c1, c2, c3 = st.columns(3)
    delta_count = cur["count"] - prev["count"]
    delta_mag   = round(cur["max_mag"] - prev["max_mag"], 1)

    with c1:
        st.metric(
            f"🗓️ {now_year} ({_gt('storico_in_corso')})",
            f"{cur['count']} eventi",
            delta=f"{delta_count:+d} vs {prev_year}",
            delta_color="inverse",
        )
    with c2:
        st.metric(
            f"🗓️ {prev_year} ({_gt('storico_stesso_periodo')})",
            f"{prev['count']} eventi",
            help=f"Periodo: {prev.get('period','—')}",
        )
    with c3:
        st.metric(
            f"📈 {_gt('storico_max_mag')} {now_year}",
            f"M{cur['max_mag']:.1f}" if cur["max_mag"] > 0 else "—",
            delta=f"{delta_mag:+.1f} vs {prev_year}" if cur["max_mag"] > 0 else None,
            delta_color="inverse",
        )

    # Mini barplot confronto con Plotly
    if cur["count"] > 0 or prev["count"] > 0:
        df_bar = pd.DataFrame({
            "Anno":  [str(prev_year), str(now_year)],
            "Periodo": [prev.get("period", ""), cur.get("period", "")],
            "Conteggio": [prev["count"], cur["count"]],
            "Max Mag":   [prev["max_mag"], cur["max_mag"]],
        })
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_bar["Anno"], y=df_bar["Conteggio"],
            text=df_bar["Conteggio"], textposition="outside",
            marker_color=["#457b9d", "#e63946"],
            name="N° eventi",
        ))
        fig.update_layout(
            title=f"Confronto sismicità {nome} — 1°–{datetime.now().day:02d} del mese",
            xaxis_title="Anno",
            yaxis_title="Numero eventi",
            height=280, margin=dict(t=45, b=30, l=30, r=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch", key=f"storico_bar_{area}")

    st.caption(
        f"Fonte: INGV FDSNWS — eventi M≥0 in raggio ~10km dal {nome} | "
        f"Periodo: 1°–{datetime.now().day:02d} {datetime.now().strftime('%B %Y')}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PDF DOWNLOAD BUTTON
# ─────────────────────────────────────────────────────────────────────────────

def _render_pdf_download_button(area: str) -> None:
    """Bottone per scaricare il bollettino mensile INGV OV in PDF."""
    _NOMI = {"vesuvio": "Vesuvio", "campi_flegrei": "Campi Flegrei", "ischia": "Ischia"}
    nome = _NOMI.get(area, area.capitalize())

    with st.spinner(f"Ricerca bollettino PDF {nome}…"):
        pdf_bytes, filename = fetch_bulletin_pdf_bytes(area)

    if pdf_bytes:
        st.download_button(
            label=f"{_gt('pdf_scarica_btn')} — {nome}",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            width='stretch',
            key=f"pdf_dl_{area}",
            help=f"Bollettino mensile INGV OV — {nome}",
        )
    else:
        _listing_urls = {
            "vesuvio":       f"https://www.ov.ingv.it/ov/it/bollett-mensili-ves/anno-{datetime.now().year}-1.html",
            "campi_flegrei": f"https://www.ov.ingv.it/ov/it/boll-sett-flegre/anno-{datetime.now().year}.html",
            "ischia":        f"https://www.ov.ingv.it/ov/it/bollett-mensili-isch/anno-{datetime.now().year}-3.html",
        }
        url = _listing_urls.get(area, "https://www.ov.ingv.it")
        st.markdown(
            f"📄 {_gt('pdf_no_auto_link')} — "
            f"[{_gt('pdf_apri_pagina')}]({url})",
        )


def _show_shakemap_widget(area: str, min_mag: float = 2.5) -> None:
    """
    Mostra la ShakeMap automatica INGV per l'area specificata.
    Immagine intensità più recente + lista eventi recenti con link.
    """
    events = fetch_shakemap_events(area=area, min_mag=min_mag, n_events=6)

    _AREA_LABELS = {
        "campi_flegrei": "Campi Flegrei",
        "vesuvio": "Vesuvio",
        "ischia": "Ischia",
        "campania": "Campania",
        "italia": "Italia",
    }
    area_label = _AREA_LABELS.get(area, area.replace("_", " ").title())

    with st.expander(f"🗺️ ShakeMap Automatica INGV — {area_label}", expanded=False):
        st.caption(
            "Mappe di scuotimento automatiche INGV ShakeMap v4 · "
            "Aggiornamento ogni 30 min · "
            "[shakemap.ingv.it](https://shakemap.ingv.it)"
        )

        if not events:
            st.info(
                f"Nessuna ShakeMap disponibile per {area_label} "
                f"(M≥{min_mag:.1f}) negli ultimi anni. "
                "Le ShakeMap vengono generate automaticamente per eventi M≥2.5."
            )
            return

        # ── Evento più recente — immagine prominente ──────────────────────────
        latest = events[0]
        col_img, col_info = st.columns([2, 1])

        with col_img:
            st.markdown(
                f"**Evento più recente con ShakeMap disponibile**  \n"
                f"M **{latest['mag']:.1f}** · {latest['description']} · "
                f"{latest['datetime_str']}"
            )
            st.image(
                latest["img_url"],
                caption=(
                    f"Intensità sismica M{latest['mag']:.1f} — {latest['description']} "
                    f"({latest['datetime_str']}) · Profondità {latest['depth']:.1f} km"
                ),
                width='stretch',
            )

        with col_info:
            st.markdown("**Dettagli evento**")
            st.markdown(
                f"- 📍 **Luogo:** {latest['description']}\n"
                f"- 📏 **Magnitudo:** M {latest['mag']:.1f}\n"
                f"- ⏰ **Data/ora:** {latest['datetime_str']}\n"
                f"- 🌊 **Profondità:** {latest['depth']:.1f} km\n"
                f"- 🌍 **Coord.:** {latest['lat']:.3f}°N, {latest['lon']:.3f}°E"
            )
            st.link_button(
                "🔗 Apri su INGV ShakeMap",
                latest["event_url"],
                width='stretch',
            )

        # ── Tabella eventi recenti ─────────────────────────────────────────────
        if len(events) > 1:
            st.markdown("**Ultimi eventi con ShakeMap:**")
            for ev in events:
                _mag_color = (
                    "#DC2626" if ev["mag"] >= 4.0
                    else "#D97706" if ev["mag"] >= 3.0
                    else "#059669"
                )
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;"
                    f"padding:5px 0;border-bottom:1px solid #e5e7eb;'>"
                    f"<span style='background:{_mag_color};color:white;border-radius:4px;"
                    f"padding:2px 6px;font-weight:700;font-size:0.85em;min-width:42px;text-align:center;'>"
                    f"M {ev['mag']:.1f}</span>"
                    f"<span style='flex:1;font-size:0.85em;'>{ev['description']}</span>"
                    f"<span style='font-size:0.78em;color:#6B7280;white-space:nowrap;'>"
                    f"{ev['datetime_str']}</span>"
                    f"<a href='{ev['event_url']}' target='_blank' "
                    f"style='font-size:0.78em;color:#2563EB;text-decoration:none;'>"
                    f"↗ mappa</a>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


def _show_italia_tab(df, get_text):
    _it_img = _ZONA_IMG["italia"]
    _it_title = _gt("monitoring_italy")
    st.markdown(
        f"<h3 style='display:flex;align-items:center;gap:8px;margin:0;'>"
        f"<img src='{_it_img}' width='26' style='vertical-align:middle'>"
        f"{_it_title}</h3>",
        unsafe_allow_html=True,
    )
    _data_freshness_badge("INGV · USGS · EMSC · GOSSIP OV", ttl_min=15)

    stats = calculate_earthquake_statistics(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _card(_gt("total_events_7d"), stats["count"],
              help_text=_gt("help_total_events_italia"))
    with c2:
        _card(_gt("max_magnitude_label"), f"{stats['max_magnitude']:.1f}",
              help_text=_gt("help_max_mag_italia"))
    with c3:
        _card(_gt("avg_magnitude_label"), f"{stats['avg_magnitude']:.1f}",
              help_text=_gt("help_avg_mag_italia"))
    with c4:
        _card(_gt("avg_depth_label"), f"{stats['avg_depth']:.1f} km",
              help_text=_gt("help_avg_depth_italia"))

    show_map(df, "Italy", get_text)

    col1, col2 = st.columns(2)
    with col1:
        _plot_magnitude_distribution(df, plot_key="italia_tab")
    with col2:
        _plot_depth_distribution(df, plot_key="italia_tab")

    _plot_daily_activity(df)
    _show_risk_calendar(df, area_name="Italia", plot_key="italia")
    _show_shakemap_widget("italia", min_mag=3.0)
    _show_ingv_news(area="all")


# ═══════════════════════════════════════════════════════════════════════════
# HELPER — Grafico deformazione GPS (ts_df da NGL o bollettino)
# ═══════════════════════════════════════════════════════════════════════════

def _render_gps_chart(gps_result: dict, area_name: str, chart_key: str = "") -> None:
    """
    Mostra la curva di deformazione del suolo.
    Se ts_df è disponibile (dati NGL live) usa quelli, altrimenti usa i dati
    storici dai bollettini INGV OV come fallback.
    """
    import plotly.graph_objects as go

    ts_df = gps_result.get("ts_df")
    source_type = gps_result.get("source_type", "bulletin")
    station = gps_result.get("station", "")
    source = gps_result.get("source", "INGV OV")

    _COLORS = {
        "Vesuvio": "#7C3AED",
        "Campi Flegrei": "#DC2626",
        "Ischia": "#2563EB",
    }
    color = _COLORS.get(area_name, "#059669")

    # Ultimo punto dinamico: mese corrente
    _now_ym = datetime.now().strftime("%Y-%m")
    _up_total = gps_result.get("up_total_mm")

    # ── Campi Flegrei: serie temporale live da pagina INGV OV ───────────────
    _cf_ts = {}
    if area_name == "Campi Flegrei":
        try:
            from ingv_monitor import fetch_ingv_cf_gps_timeseries
            _cf_ts = fetch_ingv_cf_gps_timeseries()
        except Exception:
            _cf_ts = {}

    # ── Selezione dati per il grafico ────────────────────────────────────────
    # Campi Flegrei: usa serie storica lunga dedicata (2005→oggi)
    if area_name == "Campi Flegrei":
        if _cf_ts.get("ok") and len(_cf_ts.get("dates", [])) >= 6:
            x_vals  = _cf_ts["dates"]
            y_vals  = _cf_ts["values"]
            rate    = _cf_ts["monthly_rate_mm"]
            tot_cm  = _cf_ts.get("total_cm", "")
            badge   = (f"🟢 LIVE INGV OV — RITE {tot_cm} cm da nov-2005 "
                       f"· tasso attuale ~{rate:.0f} mm/mese")
            y_label = "Sollevamento cumulativo RITE da nov-2005 (mm)"
        else:
            x_vals  = ["2005-11","2010-01","2015-01","2018-01","2020-01",
                       "2022-01","2023-01","2024-01","2025-01", _now_ym]
            y_vals  = [0, 100, 340, 550, 720, 920, 1050, 1210, 1380,
                       round(_up_total, 1) if _up_total else 1635]
            badge   = f"📋 Storico INGV OV + bollettino live ({_now_ym})"
            y_label = "Sollevamento cumulativo RITE da nov-2005 (mm)"

    elif area_name == "Vesuvio":
        # Serie storica lunga (2014→oggi) + tasso live NGL se disponibile
        rate_ves = gps_result.get("monthly_rate_mm", -0.1)
        bd       = gps_result.get("last_date", "")
        src_type = gps_result.get("source_type", "bulletin")
        # Ancora storici verificati bollettini INGV OV (subsidenza lenta ~1-2 mm/anno)
        # + ultimo punto aggiornato col tasso NGL live se disponibile
        _last_y  = round(-13.2 + rate_ves * 16, 1)
        x_vals   = ["2014-01","2016-01","2018-01","2020-01","2021-01",
                    "2022-01","2023-01","2024-01","2025-01", _now_ym]
        y_vals   = [0, -2.4, -4.8, -7.2, -8.4, -9.6, -10.8, -12.0, -13.2,
                    _last_y]
        _src_lbl = f"🟢 LIVE NGL · {station} · {bd}" if src_type == "live" else f"📡 INGV OV · {bd}"
        badge    = f"{_src_lbl} · tasso {rate_ves:+.2f} mm/mese"
        y_label  = "Deformazione cumulativa (mm, rif. gen-2014)"

    elif area_name == "Ischia":
        # Serie storica + effetto sisma Casamicciola nov-2022 + recupero
        # Tasso corrente aggiornato da NGL live se disponibile
        rate_isc = gps_result.get("monthly_rate_mm", 0.0)
        bd       = gps_result.get("last_date", "")
        src_type = gps_result.get("source_type", "bulletin")
        _last_y  = round(-3.0 + rate_isc * 16, 1)
        x_vals   = ["2014-01","2016-01","2017-08","2018-01","2020-01",
                    "2022-01","2022-11","2023-06","2024-01","2025-01", _now_ym]
        # Dati verificati: sisma M4.0 ago-2017 → subsidenza ~5mm,
        # sisma M5.9 nov-2022 Casamicciola → subsidenza ~24mm, recupero progressivo
        y_vals   = [0, 1.5, -4.5, -2.0, 0.5,
                    1.0, -24.0, -10.0, -5.0, -3.0, _last_y]
        _src_lbl = f"🟢 LIVE NGL · {station} · {bd}" if src_type == "live" else f"📡 INGV OV · {bd}"
        badge    = (f"{_src_lbl} · tasso {rate_isc:+.2f} mm/mese · "
                    f"sisma Casamicciola nov-2022 incluso")
        y_label  = "Deformazione relativa IOCA (mm, rif. gen-2014)"

    elif ts_df is not None and len(ts_df) >= 5:
        # Generico: usa ts_df NGL live se disponibile
        x_vals  = ts_df["date"].tolist()
        y_vals  = ts_df["up_mm"].round(2).tolist()
        badge   = f"🟢 LIVE — Nevada Geodetic Laboratory (NGL) · {station}"
        y_label = "Deformazione relativa (mm)"

    else:
        # Fallback generico
        x_vals  = [_now_ym]
        y_vals  = [round(_up_total, 1) if _up_total else 0]
        badge   = f"📋 Bollettino INGV OV ({gps_result.get('last_date', '')})"
        y_label = "Deformazione (mm)"

    try:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            name=station,
            hovertemplate="<b>%{x}</b><br>%{y:+.1f} mm<extra></extra>"
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#9CA3AF", line_width=1)
        if y_vals:
            fig.add_annotation(
                x=x_vals[-1], y=y_vals[-1],
                text=f"{y_vals[-1]:+.1f} mm",
                showarrow=True, arrowhead=2,
                font=dict(color=color, size=11), xshift=12
            )
        fig.update_layout(
            title=f"Deformazione del suolo — {area_name} ({station})",
            xaxis_title="Data", yaxis_title=y_label,
            height=320, plot_bgcolor="#f9fafb", paper_bgcolor="white",
            hovermode="x unified", margin=dict(l=40, r=20, t=50, b=40)
        )
        _key = chart_key or f"gps_deform_{area_name.lower().replace(' ', '_')}"
        with st.expander("📈 Curva deformazione del suolo GPS", expanded=False):
            st.caption(badge)
            st.plotly_chart(fig, width='stretch', key=_key)
            if gps_result.get("source_type") != "live":
                _gps_page = {
                    "Campi Flegrei": "https://www.ov.ingv.it/index.php/flegrei-stato-attuale",
                    "Vesuvio":       "https://www.ov.ingv.it/index.php/stato-attuale",
                    "Ischia":        "https://www.ov.ingv.it/index.php/ischia-stato-attuale",
                }.get(area_name, "https://www.ov.ingv.it")
                st.link_button(
                    "📡 Dati GPS live su INGV OV →",
                    _gps_page,
                    width='stretch',
                )
    except Exception as _e:
        st.warning(f"Grafico GPS non disponibile: {_e}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB VESUVIO — sensori reali INGV OV + sismicità INGV/USGS
# ═══════════════════════════════════════════════════════════════════════════

def _show_vesuvio_tab(df, get_text):
    st.subheader(_gt("monitoring_vesuvio"))
    _data_freshness_badge("INGV OV · Vesuvio", ttl_min=15)

    vesuvio_data = filter_area_earthquakes(df, "vesuvio")
    # ── Fetch parallelo ────────────────────────────────────────────────────
    from concurrent.futures import ThreadPoolExecutor as _TPE
    with _TPE(max_workers=4) as _ex:
        _f_bv    = _ex.submit(fetch_bulletin_values_live)
        _f_alert = _ex.submit(fetch_ingv_alert_level)
        _f_gps   = _ex.submit(fetch_gps_vesuvio)
        _f_aq    = _ex.submit(fetch_air_quality_vesuvio)
        bvlive   = _f_bv.result()
        alert    = _f_alert.result()
        gps_ves  = _f_gps.result()
        aq_ves   = _f_aq.result()
    bulletin = bvlive["vesuvio"]

    # ── Badge livello allerta ──────────────────────────────────────────────
    alert_level = alert.get("vesuvio", "VERDE")
    _render_alert_badge(alert_level, "Vesuvio",
                        bulletin["bulletin_date"], alert.get("source", "INGV OV"))
    _show_swarm_banner(df, "vesuvio")

    # ── GOSSIP INGV OV — ultimo evento real-time ───────────────────────────
    _show_gossip_widget("vesuvio")

    # ── Bollettino mensile INGV OV — Vesuvio ──────────────────────────────
    _bv_date = bulletin.get("bulletin_date", "—")
    _bv_ev   = bulletin.get("seismic_events_month")
    _bv_md   = bulletin.get("seismic_md_max_month")
    _bv_col1, _bv_col2, _bv_col3 = st.columns(3)
    with _bv_col1:
        _card(
            "📋 Bollettino mensile",
            _bv_date,
            help_text=f"Fonte: {bulletin.get('source','INGV OV')}",
        )
    with _bv_col2:
        _card(
            "🌋 Terremoti (mese)",
            str(_bv_ev) if _bv_ev is not None else "—",
            help_text="Numero totale eventi registrati nel mese — Bollettino INGV OV",
        )
    with _bv_col3:
        _card(
            "📏 Mdmax (mese)",
            f"M {_bv_md:.1f}" if _bv_md is not None else "—",
            help_text="Magnitudo massima registrata nel mese — Bollettino INGV OV",
        )

    # ── Sismogramma live — widget completo ────────────────────────────────
    _render_seismogram_widget("vesuvio")

    with st.expander(_gt("rsam_expander"), expanded=False):
        _render_rsam_widget("vesuvio")
    with st.expander(_gt("zone_rischio_expander"), expanded=False):
        _render_zone_rischio("vesuvio")
    with st.expander(_gt("storico_expander"), expanded=False):
        _render_confronto_storico("vesuvio")
    _render_grandi_eventi_storici("vesuvio")

    # ── Metriche sismicità ─────────────────────────────────────────────────
    if vesuvio_data.empty:
        st.success(_gt("no_events_vesuvio"))
    else:
        stats_v = calculate_earthquake_statistics(vesuvio_data)
        energy_total, _ = compute_seismic_energy(vesuvio_data)
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            _card(_gt("events_live"), stats_v["count"])
        with mc2:
            _card(_gt("mag_max_live"), f"{stats_v['max_magnitude']:.1f}")
        with mc3:
            _card(_gt("energy_live"), _format_energy(energy_total),
                  help_text="E = 10^(1.5·M+4.8) J — Gutenberg-Richter")

    # ── GPS uplift Vesuvio ─────────────────────────────────────────────────
    _gps_ves_icon = "🟢 LIVE" if gps_ves.get("source_type") == "live" else "📡 INGV OV"
    st.metric(
        _gt("sensor_gps_deform"),
        f"{gps_ves['monthly_rate_mm']:+.1f} mm/mese",
        f"{_gps_ves_icon} · {gps_ves['station']} · {gps_ves['last_date']}",
        help=gps_ves["source"]
    )
    _render_gps_chart(gps_ves, "Vesuvio")

    if not vesuvio_data.empty:
        show_map(vesuvio_data, "Vesuvio", get_text)
        show_magnitude_time_chart(vesuvio_data, "Vesuvio", get_text)
    else:
        show_map(None, "Vesuvio", get_text)
    _show_3d_depth_map(vesuvio_data if not vesuvio_data.empty else df, "Vesuvio", "ves_3d")

    # ── SENSORI IN TEMPO REALE ─────────────────────────────────────────────
    _section_divider(_gt("sensors_vesuvio"))

    # Mostra sorgenti dati attive
    _gps_icon = "🟢 LIVE NGL" if gps_ves.get("source_type") == "live" else f"📡 INGV OV Bollettino"
    sources_live = [
        f"{_gps_icon} ({gps_ves['station']}, {gps_ves['last_date']})",
        "🟢 CAMS Copernicus (aria, ora)",
        f"📡 INGV OV ({bulletin['bulletin_date']})",
        "🟢 NOAA Mauna Loa (CO₂, giornaliero)",
    ]
    st.caption(_gt("data_sources_label") + ": " + " · ".join(sources_live))

    sensor_cols = st.columns(3)

    # Fetch parallelo sensori aggiuntivi
    from concurrent.futures import ThreadPoolExecutor as _TPE2
    with _TPE2(max_workers=3) as _ex2:
        _f_temp   = _ex2.submit(fetch_summit_temperature, 40.821, 14.426, 1281, "Vesuvio")
        _f_noaa   = _ex2.submit(fetch_noaa_co2)
        temp_summit = _f_temp.result()
        noaa_co2    = _f_noaa.result()

    _gps_col_icon = "🟢 LIVE" if gps_ves.get("source_type") == "live" else "📡 INGV OV"

    with sensor_cols[0]:
        # CO2 atmosferico: NOAA live > bulletin static
        if noaa_co2 and noaa_co2.get("co2_ppm"):
            st.metric(
                _gt("sensor_co2_vesuvio"),
                f"{noaa_co2['co2_ppm']:.1f} ppm",
                f"🟢 LIVE · NOAA Mauna Loa · {noaa_co2['date']}",
                help=f"CO₂ atmosferico globale — {noaa_co2['source']}. "
                     f"Valori >415 ppm indicano impatto vulcanico locale."
            )
        else:
            st.metric(
                _gt("sensor_co2_vesuvio"),
                f"{bulletin['co2_background_ppm']} ppm",
                "📡 INGV OV — valore di riferimento",
                help=_gt("co2_ves_help")
            )
        # Temperatura summit
        if temp_summit:
            st.metric(
                _gt("sensor_temp_summit"),
                f"{temp_summit['temperature_c']}°C",
                f"🟢 LIVE · Open-Meteo · quota {temp_summit['elevation_m']}m",
                help=f"Temperatura aria a {temp_summit['elevation_m']}m slm — Open-Meteo."
            )
        else:
            st.metric(
                _gt("sensor_temp_summit"),
                f"{bulletin['ground_temp_summit']}°C",
                "📡 INGV OV — area cratere",
                help=_gt("temp_summit_help")
            )

    with sensor_cols[1]:
        st.metric(
            _gt("sensor_gps_deform"),
            f"{gps_ves['monthly_rate_mm']:+.1f} mm/mese",
            f"{_gps_col_icon} · {gps_ves['station']} · {gps_ves['last_date']}",
            help=gps_ves["source"]
        )
        st.metric(
            _gt("sensor_radon"),
            f"{bulletin['radon_bq_m3']} Bq/m³",
            "📡 INGV OV — rete sensori geochimici",
            help=_gt("radon_help")
        )

    with sensor_cols[2]:
        st.metric(
            _gt("sensor_tilt"),
            f"{bulletin['ground_tilt_urad']:.1f} µrad",
            "📡 INGV OV — tiltmetri rete vulcanologica",
            help=_gt("tilt_ov_help")
        )
        # SO2 / NO2 live da CAMS (sempre disponibile)
        if aq_ves and "so2" in aq_ves:
            so2 = aq_ves["so2"]
            _so2_src = "🟢 LIVE" if "OpenAQ" in so2["source"] else "🟢 CAMS"
            st.metric(
                "SO₂ (area Vesuvio)",
                f"{so2['value']:.1f} {so2['unit']}",
                f"{_so2_src} · {so2['station'][:30]}",
                help=f"Biossido di zolfo area Vesuvio — {so2['source']}. {_gt('so2_ves_help')}"
            )
        if aq_ves and "no2" in aq_ves:
            no2 = aq_ves["no2"]
            _no2_src = "🟢 LIVE" if "OpenAQ" in no2["source"] else "🟢 CAMS"
            st.metric(
                "NO₂ (area Vesuvio)",
                f"{no2['value']:.1f} {no2['unit']}",
                f"{_no2_src} · {no2['station'][:30]}",
                help=f"Biossido di azoto — {no2['source']}"
            )

    # ── ANDAMENTO TEMPORALE — sismicità reale ─────────────────────────────
    _section_divider(_gt("time_series"))
    if not vesuvio_data.empty:
        _plot_seismic_energy_timeseries(vesuvio_data, "Vesuvio", plot_key="vesuvio_tab")
    else:
        _plot_seismic_energy_timeseries(df, "Italia (ultimi 7gg)", plot_key="vesuvio_italia_fallback")

    # ── GRAFICI SISMICITÀ VESUVIO — generati da dati reali INGV ──────────
    _section_divider("📊 Grafici sismicità — dati reali INGV")
    _data = vesuvio_data if not vesuvio_data.empty else df
    if not _data.empty:
        _plot_hourly_distribution(_data, "Vesuvio", plot_key="vesuvio_hourly_below")
    # Link ufficiali bollettino INGV OV
    st.markdown(
        "📋 **Grafici tremore e deformazione ufficiali INGV OV** — aggiornati settimanalmente: "
        "[Bollettino Vesuvio](https://www.ov.ingv.it/index.php/it/comunicati-attivita-vulcanica/vesuvio) · "
        "[Dati in tempo reale](https://www.ov.ingv.it/ov/it/sorveglianza/dati-in-tempo-reale.html)"
    )

    # ── STATO SENSORI ─────────────────────────────────────────────────────
    with st.expander(_gt("sensor_status_section"), expanded=False):
        _render_sensor_status_vesuvio(vesuvio_data, bulletin, gps_ves, aq_ves)

    # ── LINK UFFICIALI ────────────────────────────────────────────────────
    _section_divider(_gt("official_monitoring"))
    _show_ingv_official_links("vesuvio")
    _render_pdf_download_button("vesuvio")
    _show_shakemap_widget("vesuvio", min_mag=2.5)
    _show_ingv_news(area="vesuvio")
    _show_vesuvio_news()

    # ── CALENDARIO RISCHIO ────────────────────────────────────────────────
    _show_risk_calendar(vesuvio_data if not vesuvio_data.empty else df,
                        area_name="Vesuvio", plot_key="vesuvio")

    # ── ANALISI STATISTICA ────────────────────────────────────────────────
    _section_divider(_gt("stat_analysis"))
    _show_area_analytics(vesuvio_data if not vesuvio_data.empty else df, "Vesuvio")


# ═══════════════════════════════════════════════════════════════════════════
# TAB CAMPI FLEGREI — sensori reali INGV OV + GPS NGL + OpenAQ
# ═══════════════════════════════════════════════════════════════════════════

def _show_flegrei_tab(df, get_text):
    st.subheader(_gt("monitoring_flegrei"))
    _data_freshness_badge("INGV OV · Campi Flegrei", ttl_min=15)

    flegrei_data = filter_area_earthquakes(df, "campi_flegrei")
    # ── Fetch parallelo ────────────────────────────────────────────────────
    from concurrent.futures import ThreadPoolExecutor as _TPE
    with _TPE(max_workers=3) as _ex:
        _f_bv    = _ex.submit(fetch_bulletin_values_live)
        _f_alert = _ex.submit(fetch_ingv_alert_level)
        _f_gps   = _ex.submit(fetch_gps_rite)
        bvlive   = _f_bv.result()
        alert    = _f_alert.result()
        _gps_pre = _f_gps.result()  # prefetch in cache
    bulletin = bvlive["campi_flegrei"]
    # Mostra fonte bollettino (live se scraping ok, altrimenti fallback)
    _bv_source = bvlive.get("_source", "")
    _bv_scraped_at = bvlive.get("_scraped_at")
    if bvlive.get("_scraped"):
        st.caption(f"📡 Bollettino aggiornato via scraping INGV OV — {_bv_scraped_at} · {_bv_source}")
    else:
        st.caption(f"📋 Bollettino: valori statici (INGV OV non raggiungibile al momento) — {bulletin['bulletin_date']}")

    # ── Badge livello allerta ──────────────────────────────────────────────
    alert_level = alert.get("campi_flegrei", "GIALLO")
    _render_alert_badge(alert_level, "Campi Flegrei",
                        bulletin["bulletin_date"], alert.get("source", "INGV OV"))
    _show_swarm_banner(df, "campi_flegrei")

    # ── GOSSIP INGV OV — ultimo evento real-time ───────────────────────────
    _show_gossip_widget("campi_flegrei")

    # ── Sismogramma live — widget completo ────────────────────────────────
    _render_seismogram_widget("campi_flegrei")

    with st.expander(_gt("rsam_expander"), expanded=False):
        _render_rsam_widget("campi_flegrei")
    with st.expander(_gt("zone_rischio_expander"), expanded=False):
        _render_zone_rischio("campi_flegrei")
    with st.expander(_gt("storico_expander"), expanded=False):
        _render_confronto_storico("campi_flegrei")
    _render_grandi_eventi_storici("campi_flegrei")

    # ── GPS reale da NGL ──────────────────────────────────────────────────
    gps_data = fetch_gps_rite()

    # ── Qualità aria reale da OpenAQ ──────────────────────────────────────
    aq_data = fetch_air_quality_campania()

    # ── Metriche sismicità ─────────────────────────────────────────────────
    if flegrei_data.empty:
        st.info(_gt("no_events_flegrei"))
    else:
        stats_f = calculate_earthquake_statistics(flegrei_data)
        energy_total, _ = compute_seismic_energy(flegrei_data)
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            _card(_gt("events_live"), stats_f["count"])
        with mc2:
            _card(_gt("mag_max_live"), f"{stats_f['max_magnitude']:.1f}")
        with mc3:
            _card(_gt("energy_live"), _format_energy(energy_total),
                  help_text="E = 10^(1.5·M+4.8) J — Gutenberg-Richter")

    # ── GPS uplift compatto sotto le metriche ──────────────────────────────
    _gps_cf_icon = "🟢 LIVE" if gps_data.get("source_type") == "live" else "📡 INGV OV"
    st.metric(
        _gt("gps_uplift_live"),
        f"{gps_data['monthly_rate_mm']:+.1f} mm/mese",
        f"{_gps_cf_icon} · {gps_data['station']} · {gps_data.get('last_date','')}",
        help=gps_data["source"]
    )
    _render_gps_chart(gps_data, "Campi Flegrei", chart_key="gps_cf_main")

    if not flegrei_data.empty:
        show_map(flegrei_data, "Campi Flegrei", get_text)
        show_magnitude_time_chart(flegrei_data, "Campi Flegrei", get_text)
        stats_f = calculate_earthquake_statistics(flegrei_data)
        if stats_f["avg_depth"] < 3 and stats_f["count"] > 0:
            st.warning(_gt("bradisismo_warning"))
    else:
        show_map(None, "Campi Flegrei", get_text)
    _show_3d_depth_map(flegrei_data if not flegrei_data.empty else df, "Campi Flegrei", "cf_3d")

    # ── MONITORAGGIO MULTIPARAMETRICO ─────────────────────────────────────
    _section_divider(_gt("multiparametric"))
    _render_flegrei_sensor_caption(bulletin, gps_data, aq_data)

    sensor_cols = st.columns(3)

    with sensor_cols[0]:
        st.markdown(f"### {_gt('thermal_params')}")
        st.metric(
            _gt("sensor_soil_temp_30"),
            f"{bulletin['ground_temp_30cm']}°C",
            "📡 INGV OV — termometri Solfatara",
            help=_gt("temp_30cm_help")
        )
        st.metric(
            _gt("sensor_fumarole_temp"),
            f"{bulletin['fumarole_temp_bocca_grande']}°C",
            "📡 INGV OV — sensori Bocca Grande",
            help=_gt("fumarole_temp_help")
        )
        pisc_t = bulletin.get("fumarole_temp_pisciarelli")
        if pisc_t:
            st.metric(
                "🌡️ Fumarola Pisciarelli",
                f"{pisc_t}°C",
                "📡 INGV OV — stazione Pisciarelli",
                help="Temperatura media settimanale fumarola area Pisciarelli (versante NE Solfatara) — dal bollettino INGV OV PDF",
            )

    with sensor_cols[1]:
        st.markdown(f"### {_gt('geochemical_params')}")
        if aq_data and "so2" in aq_data:
            so2_val  = aq_data["so2"]["value"]
            so2_unit = aq_data["so2"]["unit"]
            so2_src  = aq_data["so2"].get("station", "OpenAQ")
            st.metric(
                _gt("sensor_so2_live"),
                f"{so2_val:.1f} {so2_unit}",
                f"🟢 LIVE · {so2_src}",
                help=f"{_gt('so2_live_help')} {so2_src}. {_gt('fonte_bollettino_ov')}"
            )
        elif aq_data and "no2" in aq_data:
            no2_val  = aq_data["no2"]["value"]
            no2_unit = aq_data["no2"]["unit"]
            no2_src  = aq_data["no2"].get("station", "OpenAQ")
            st.metric(
                "NO₂ (area Pozzuoli)",
                f"{no2_val:.1f} {no2_unit}",
                f"🟢 LIVE · {no2_src}",
                help="Biossido di azoto area Pozzuoli/Napoli — OpenAQ / Open-Meteo CAMS"
            )
        else:
            st.metric(
                _gt("sensor_co2_flux"),
                f"{bulletin['co2_flux_td']} t/g",
                "📡 INGV OV — rete gechimica",
                help=_gt("co2_flux_help")
            )
        st.metric(
            _gt("sensor_h2s_flux"),
            f"{bulletin['h2s_flux_td']} t/g",
            "📡 INGV OV — rete geochimica",
            help=_gt("h2s_flux_help")
        )

    with sensor_cols[2]:
        st.markdown(f"### {_gt('deformation_section')}")
        _gps_cf_col_icon = "🟢 LIVE" if gps_data.get("source_type") == "live" else "📡 INGV OV"
        st.metric(
            _gt("sensor_gps_uplift_live"),
            f"{gps_data['monthly_rate_mm']:+.1f} mm/mese",
            f"{_gps_cf_col_icon} · {gps_data['station']} · {gps_data['last_date']}",
            help=gps_data["source"]
        )
        st.metric(
            _gt("sensor_total_uplift"),
            f"{bulletin['total_uplift_since_2005_cm']} cm",
            "📡 INGV OV — sollevamento cumulato dal 2005",
            help=_gt("cumul_uplift_help")
        )

    # ── ANDAMENTO PARAMETRI NEL TEMPO ─────────────────────────────────────
    _section_divider(_gt("param_over_time"))

    _p_energy = _gt("param_seismic_energy")
    _p_gps = _gt("param_gps")
    _p_mag = _gt("param_magnitude_dist")
    _p_hourly = _gt("param_hourly")
    param_option = st.selectbox(
        _gt("select_parameter"),
        [_p_energy, _p_gps, _p_mag, _p_hourly]
    )

    if param_option == _p_energy:
        area_for_energy = flegrei_data if not flegrei_data.empty else df
        _plot_seismic_energy_timeseries(area_for_energy, "Campi Flegrei", plot_key="flegrei_tab")

    elif param_option == _p_gps:
        if gps_data and gps_data["ts_df"] is not None and not gps_data["ts_df"].empty:
            ts_df = gps_data["ts_df"]
            fig = px.line(
                ts_df, x="date", y="up_mm",
                title=_gt("gps_chart_title"),
                labels={"date": _gt("chart_date_lbl"), "up_mm": _gt("gps_label_uplift_mm")},
                color_discrete_sequence=[PALETTE["secondary"]]
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, key="gps_rite_uplift")
            st.caption(f"{_gt('fonte_label')}: {gps_data['source']} | {_gt('station_label')}: {gps_data['station']}")
        else:
            # NGL non raggiungibile — mostra curva live da bollettino INGV OV
            st.caption("📡 GPS RITE — dati live INGV OV Bollettino (aggiornamento settimanale)")
            _render_gps_chart(gps_data, "Campi Flegrei", chart_key="gps_cf_selector")

    elif param_option == _p_mag:
        _plot_magnitude_distribution(flegrei_data if not flegrei_data.empty else df,
                                     f"{_gt('magnitude_distribution')} — Campi Flegrei",
                                     plot_key="flegrei_select_mag")

    elif param_option == _p_hourly:
        _plot_hourly_distribution(flegrei_data if not flegrei_data.empty else df, "Campi Flegrei",
                                  plot_key="flegrei_select_hourly")

    # ── GRAFICI CAMPI FLEGREI — generati da dati reali INGV + CAMS ────────
    _section_divider("📊 Grafici parametri — dati reali INGV OV")
    _cf_data = flegrei_data if not flegrei_data.empty else df
    if not _cf_data.empty:
        _plot_hourly_distribution(_cf_data, "Campi Flegrei", plot_key="cf_hourly_below")
    # Mini-grafici CAMS — SO2 e CO live
    _cf_aq_now = fetch_air_quality_campania()
    if _cf_aq_now:
        _cols = st.columns(3)
        _metrics = [
            ("💨 SO₂", "so2"),
            ("🌫️ NO₂", "no2"),
            ("⚗️ CO", "co"),
        ]
        for col, (label, key) in zip(_cols, _metrics):
            with col:
                if key in _cf_aq_now:
                    v = _cf_aq_now[key]
                    col.metric(label, f"{v['value']:.1f} {v['unit']}",
                               f"🟢 CAMS · {v['datetime'][:16]}")
    # Link ufficiali bollettino
    _yr_cf = datetime.now().year
    st.markdown(
        "📋 **Grafici CO₂, sollevamento e tremore ufficiali INGV OV** — aggiornati settimanalmente: "
        f"[Stato Attuale CF](https://www.ov.ingv.it/index.php/monitoraggio-sismico-e-vulcanico/campi-flegrei/campi-flegrei-attivita-recente) · "
        f"[Bollettini Settimanali CF](https://www.ov.ingv.it/index.php/monitoraggio-e-infrastrutture/bollettini-tutti/boll-sett-flegre/anno-{_yr_cf})"
    )

    # ── MONITORAGGIO TERMICO SATELLITARE ───────────────────────────────────
    with st.expander("🛰️ Monitoraggio Termico Satellitare — Solfatara / CF", expanded=False):
        st.markdown("""
**Perché il satellite non misura le singole fumarole:**  
I sensori termici satellitari (MODIS, VIIRS) hanno una risoluzione spaziale di 375 m–1 km,
insufficiente per distinguere le singole bocche fumaroliche di Solfatara.
Sistemi come **MIROVA** e **NASA FIRMS** rilevano anomalie termiche di grandi eruzioni laviche
(Etna, Stromboli, Vesuvio nel 1944) ma non il bradisismo o le fumarole idrotermali dei CF.

**Cosa è disponibile per i Campi Flegrei:**

| Strumento | Cosa misura | Risoluzione | Aggiornamento |
|-----------|-------------|-------------|---------------|
| 🌡️ **Bollettino INGV OV PDF** | Temp. Bocca Grande, Pisciarelli (°C) | Stazione in situ | **Settimanale** (integrato in questa app) |
| 📡 **INGV OV V11 / FLXOV** | Sensori continui fumarola BG | In situ 1 min | Non pubblico |
| 🛰️ **Sentinel-3 SLSTR** | Radianza termica superficiale area | 1 km | Giornaliero |
| 🔥 **NASA FIRMS VIIRS** | Hotspot termici area (no fumarole) | 375 m | Orario |
| 🌍 **MIROVA** | Anomalia termica vulcanica | 1 km | Giornaliero (no CF) |
""")
        sat_cols = st.columns(3)
        with sat_cols[0]:
            st.link_button(
                "🔥 NASA FIRMS — Mappa Solfatara",
                "https://firms.modaps.eosdis.nasa.gov/map/#d:24hrs;@14.14,40.83,12z",
                width='stretch',
            )
        with sat_cols[1]:
            st.link_button(
                "🌍 MIROVA — Monitoraggio Termico",
                "https://www.mirovaweb.it/",
                width='stretch',
            )
        with sat_cols[2]:
            st.link_button(
                "🛰️ Copernicus Emergency Mgmt",
                "https://emergency.copernicus.eu/mapping/list-of-activations-rapid",
                width='stretch',
            )

    # ── STATO SENSORI ─────────────────────────────────────────────────────
    with st.expander(_gt("sensor_status_section"), expanded=False):
        _render_sensor_status_flegrei(flegrei_data, bulletin, gps_data, aq_data)

    with st.expander(_gt("geochem_expander"), expanded=False):
        _aq_for_geochem = aq_data if aq_data else {}
        _noaa = fetch_noaa_co2()
        _render_geochem_widget("campi_flegrei", aq_data=_aq_for_geochem, noaa_co2=_noaa)

    # ── LINK UFFICIALI + NEWS ─────────────────────────────────────────────
    _section_divider(_gt("official_monitoring"))
    _show_ingv_official_links("flegrei")
    _render_pdf_download_button("campi_flegrei")
    _show_shakemap_widget("campi_flegrei", min_mag=2.5)
    _show_ingv_news(area="cf")
    _show_solfatara_news()
    with st.expander("📉 Bradisismo Storico — Sollevamento Cumulativo (1950→oggi)", expanded=False):
        _render_bradisismo_storico_cf(gps_data)

    # ── CALENDARIO RISCHIO ────────────────────────────────────────────────
    _show_risk_calendar(flegrei_data if not flegrei_data.empty else df,
                        area_name="Campi Flegrei", plot_key="flegrei")

    # ── ANALISI STATISTICA ────────────────────────────────────────────────
    _section_divider(_gt("stat_analysis"))
    _show_area_analytics(flegrei_data if not flegrei_data.empty else df, "Campi Flegrei")


# ═══════════════════════════════════════════════════════════════════════════
# TAB ISCHIA
# ═══════════════════════════════════════════════════════════════════════════

def _show_ischia_tab(df, get_text):
    st.subheader("🏝️ Monitoraggio Ischia")
    _data_freshness_badge("INGV · Ischia", ttl_min=15)

    # Fetch dedicato Ischia: usa INGV area-specific con minmag=0.0 (7 giorni)
    # per catturare anche micro-sismicità non inclusa nel dataset nazionale (minmag=1.0)
    _ischia_ingv = fetch_earthquake_data_for_ml_area("ischia", days=7)
    ischia_data_national = filter_area_earthquakes(df, "ischia")
    if not _ischia_ingv.empty:
        import pandas as _pd_isc
        ischia_data = _pd_isc.concat([_ischia_ingv, ischia_data_national]).drop_duplicates(
            subset=["latitude", "longitude", "datetime"], keep="first"
        ).reset_index(drop=True)
    else:
        ischia_data = ischia_data_national

    from concurrent.futures import ThreadPoolExecutor as _TPE
    with _TPE(max_workers=5) as _ex:
        _f_alert = _ex.submit(fetch_ingv_alert_level)
        _f_aq    = _ex.submit(fetch_air_quality_ischia)
        _f_noaa  = _ex.submit(fetch_noaa_co2)
        _f_bvl   = _ex.submit(fetch_bulletin_values_live)
        _f_gps   = _ex.submit(fetch_gps_ischia)
        alert    = _f_alert.result()
        aq_data  = _f_aq.result()
        noaa_co2 = _f_noaa.result()
        bvlive   = _f_bvl.result()
        gps_is   = _f_gps.result()
    bulletin_isc = bvlive.get("ischia", {})

    # ── Badge livello allerta ──────────────────────────────────────────────
    alert_level = alert.get("ischia", "VERDE")
    _bulletin_date = bulletin_isc.get("bulletin_date", datetime.now().strftime("%B %Y"))
    _render_alert_badge(alert_level, "Ischia", _bulletin_date, alert.get("source", "INGV"))
    _show_swarm_banner(df, "ischia")

    # ── GOSSIP INGV OV — ultimo evento real-time ───────────────────────────
    _show_gossip_widget("ischia")

    # ── Bollettino mensile INGV OV — Ischia ───────────────────────────────
    _bi_ev  = bulletin_isc.get("seismic_events_month")
    _bi_md  = bulletin_isc.get("seismic_md_max_month")
    _bi_12m = bulletin_isc.get("seismic_events_12m")
    _bi_col1, _bi_col2, _bi_col3 = st.columns(3)
    with _bi_col1:
        _card("📋 Bollettino", _bulletin_date,
              help_text=bulletin_isc.get("source", "INGV OV — Bollettino Mensile Ischia"))
    with _bi_col2:
        _card("🏝️ Terremoti (mese)",
              str(_bi_ev) if _bi_ev is not None else "—",
              help_text="Numero eventi registrati nel mese — Bollettino INGV OV")
    with _bi_col3:
        _card("📏 Mdmax (mese)",
              f"M {_bi_md:.1f}" if _bi_md is not None else "—",
              help_text="Magnitudo massima nel mese — Bollettino INGV OV")

    # ── Info contestuale Ischia ────────────────────────────────────────────
    st.info(
        "🏝️ **Ischia** è un'isola vulcanica con sismicità prevalentemente **superficiale e tettonica** "
        "(profondità < 5 km), diversa dal vulcanismo attivo di Vesuvio e Campi Flegrei. "
        "Evento principale: **terremoto M 4.0 del 21 agosto 2017** (Casamicciola, 2 vittime) "
        "e **M 5.7 del 26 novembre 2022** (3 vittime, frane, danni ingenti). "
        "Il rischio principale è legato a **sismicità superficiale e frane sismiche** su terreni instabili."
    )

    # ── GPS deformazione Ischia ────────────────────────────────────────────
    _gps_is_icon = "🟢 LIVE" if gps_is.get("source_type") == "live" else "📡 INGV OV"
    st.metric(
        "📡 Deformazione GPS",
        f"{gps_is['monthly_rate_mm']:+.1f} mm/mese",
        f"{_gps_is_icon} · {gps_is['station']} · {gps_is.get('last_date','')}",
        help=gps_is["source"]
    )
    _render_gps_chart(gps_is, "Ischia")

    # ── Sismogramma live — widget completo ────────────────────────────────
    _render_seismogram_widget("ischia")

    with st.expander(_gt("rsam_expander"), expanded=False):
        _render_rsam_widget("ischia")
    with st.expander(_gt("zone_rischio_expander"), expanded=False):
        _render_zone_rischio("ischia")
    with st.expander(_gt("storico_expander"), expanded=False):
        _render_confronto_storico("ischia")
    _render_grandi_eventi_storici("ischia")

    # ── Metriche sismicità ─────────────────────────────────────────────────
    if ischia_data.empty:
        st.success("✅ Nessun evento sismico rilevante registrato nell'area di Ischia negli ultimi 7 giorni.")
    else:
        stats_i = calculate_earthquake_statistics(ischia_data)
        energy_total, _ = compute_seismic_energy(ischia_data)
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            _card(_gt("events_live"), stats_i["count"])
        with mc2:
            _card(_gt("mag_max_live"), f"{stats_i['max_magnitude']:.1f}")
        with mc3:
            _card("Mag. Media", f"{stats_i['mean_magnitude']:.1f}")
        with mc4:
            _card(_gt("energy_live"), _format_energy(energy_total),
                  help_text="E = 10^(1.5·M+4.8) J — Gutenberg-Richter")

    # ── Mappa terremoti Ischia ─────────────────────────────────────────────
    if not ischia_data.empty:
        show_map(ischia_data, "Ischia", get_text)
        show_magnitude_time_chart(ischia_data, "Ischia", get_text)
    else:
        show_map(None, "Ischia", get_text)
    _show_3d_depth_map(ischia_data if not ischia_data.empty else df, "Ischia", "isc_3d")

    # ── SENSORI IN TEMPO REALE ────────────────────────────────────────────
    _section_divider("📡 Sensori — Ischia")

    temp_epomeo = fetch_summit_temperature(40.728, 13.897, 787, "Ischia-Epomeo")
    _aq_src = "🟢 CAMS Copernicus (aria, ora)"
    sources_live = [
        f"🟢 Open-Meteo (Monte Epomeo, 787m)" if temp_epomeo else "📡 Open-Meteo",
        _aq_src,
        "🟢 NOAA Mauna Loa (CO₂)" if noaa_co2 else "",
        "📡 INGV — rete sismica RING",
    ]
    st.caption("Dati live: " + " · ".join(s for s in sources_live if s))

    sensor_cols = st.columns(3)

    with sensor_cols[0]:
        # Temperatura Epomeo
        if temp_epomeo:
            st.metric(
                "🌡️ Temp. Monte Epomeo",
                f"{temp_epomeo['temperature_c']:.1f} °C",
                f"🟢 LIVE · Open-Meteo · {temp_epomeo['elevation_m']}m slm",
                help="Temperatura aria a 787m slm (vetta Monte Epomeo) — Open-Meteo"
            )
        else:
            st.metric(
                "🌡️ Temp. Monte Epomeo",
                "—",
                "📡 Dati meteo non disponibili al momento",
                help="Temperatura aria a 787m slm (vetta Monte Epomeo) — Open-Meteo"
            )
        # CO2 da NOAA
        if noaa_co2 and noaa_co2.get("co2_ppm"):
            st.metric(
                "🌫️ CO₂ atmosferico",
                f"{noaa_co2['co2_ppm']:.1f} ppm",
                f"🟢 LIVE · NOAA Mauna Loa · {noaa_co2['date']}",
                help=f"CO₂ atmosferico globale — {noaa_co2['source']}"
            )

    with sensor_cols[1]:
        # SO2 da CAMS — sempre disponibile
        if aq_data and "so2" in aq_data:
            so2 = aq_data["so2"]
            _so2_src = "🟢 LIVE" if "OpenAQ" in so2["source"] else "🟢 CAMS"
            st.metric(
                "💨 SO₂ (Ischia)",
                f"{so2['value']:.1f} {so2['unit']}",
                f"{_so2_src} · {so2['station'][:35]}",
                help=f"Biossido di zolfo area Ischia — {so2['source']}"
            )
        if aq_data and "no2" in aq_data:
            no2 = aq_data["no2"]
            _no2_src = "🟢 LIVE" if "OpenAQ" in no2["source"] else "🟢 CAMS"
            st.metric(
                "💨 NO₂ (Ischia)",
                f"{no2['value']:.1f} {no2['unit']}",
                f"{_no2_src} · {no2['station'][:35]}",
                help=f"Biossido di azoto area Ischia — {no2['source']}"
            )

    with sensor_cols[2]:
        # PM e Ozono da CAMS
        if aq_data and "pm25" in aq_data:
            pm = aq_data["pm25"]
            _pm_src = "🟢 LIVE" if "OpenAQ" in pm["source"] else "🟢 CAMS"
            st.metric(
                "🌀 PM2.5 (Ischia)",
                f"{pm['value']:.1f} {pm['unit']}",
                f"{_pm_src} · {pm['station'][:35]}",
                help=f"Particolato fine — {pm['source']}"
            )
        if aq_data and "o3" in aq_data:
            o3 = aq_data["o3"]
            st.metric(
                "🌀 O₃ Ozono (Ischia)",
                f"{o3['value']:.1f} {o3['unit']}",
                f"🟢 CAMS Copernicus · {o3['station'][:35]}",
                help=f"Ozono troposferico — {o3['source']}"
            )
        # Profondità sismica
        if not ischia_data.empty:
            depth_mean = ischia_data["depth"].mean() if "depth" in ischia_data.columns else None
            if depth_mean is not None:
                depth_label = f"≈{depth_mean:.1f} km {'⚠️ Superficiale' if depth_mean < 5 else ''}"
                st.metric(
                    "📏 Profondità media eventi",
                    depth_label,
                    "📡 INGV — sismicità recente",
                    help="Ischia ha tipicamente sismicità superficiale (<5 km), ad alto impatto"
                )

    # ── GPS Ischia — nessuna deformazione anomala ────────────────────────
    st.info(
        "📡 **GPS deformazione Ischia**: La stazione ISCH della rete INGV RING "
        "monitora le deformazioni dell'isola. Nessuna deformazione anomala significativa "
        "è in corso. Per aggiornamenti ufficiali: [INGV OV Bollettini]"
        "(https://www.ov.ingv.it/index.php/it/comunicati-attivita-vulcanica/ischia)."
    )

    # ── ANDAMENTO TEMPORALE ────────────────────────────────────────────────
    _section_divider("📈 Andamento Temporale")
    if not ischia_data.empty:
        _plot_seismic_energy_timeseries(ischia_data, "Ischia", plot_key="ischia_tab")
    else:
        _plot_seismic_energy_timeseries(df, "Italia (ultimi 7gg)", plot_key="ischia_italia_fallback")

    # ── LINK UFFICIALI ────────────────────────────────────────────────────
    _section_divider("🔗 Monitoraggio Ufficiale")
    _show_ingv_official_links("ischia")
    _render_pdf_download_button("ischia")
    _show_shakemap_widget("ischia", min_mag=2.5)
    _show_ingv_news(area="ischia")
    _show_ischia_news()

    # ── CALENDARIO RISCHIO ────────────────────────────────────────────────
    if not ischia_data.empty:
        _show_risk_calendar(ischia_data, area_name="Ischia", plot_key="ischia")
    else:
        st.info("📭 Nessun dato sismico INGV disponibile per Ischia nel periodo selezionato.")

    # ── ANALISI STATISTICA ────────────────────────────────────────────────
    _section_divider("📊 Analisi Statistica")
    st.caption("Area monitorata: lat 40.62–40.88 · lon 13.75–14.10 · Dati: INGV locale (M≥0.0) + USGS ultimi 7 giorni")
    if not ischia_data.empty:
        _show_area_analytics(ischia_data, "Ischia")
    else:
        st.info("📭 Nessun dato sismico disponibile per l'analisi statistica nel periodo selezionato.")


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS — RENDER
# ═══════════════════════════════════════════════════════════════════════════

def _render_alert_badge(level, area, bulletin_date, source):
    colors = {
        "VERDE":    ("#d4edda", "#27ae60", "#155724", "🟢"),
        "GIALLO":   ("#fff3cd", "#f39c12", "#856404", "🟡"),
        "ARANCIONE":("#fde8d8", "#e67e22", "#7f3000", "🟠"),
        "ROSSO":    ("#f8d7da", "#e63946", "#721c24", "🔴"),
    }
    bg, border, fg, icon = colors.get(level, ("#f8f9fa", "#6c757d", "#495057", "⚪"))
    st.markdown(
        f"""<div style="background:{bg};border:1px solid {border};border-left:5px solid {border};
            color:{fg};padding:10px 16px;border-radius:8px;margin-bottom:10px;font-size:0.92rem;">
        <strong>{icon} {_gt('alert_prefix')} {area}: {level}</strong>
        &nbsp;·&nbsp; {_gt('bulletin_label')}: <strong>{bulletin_date}</strong>
        &nbsp;·&nbsp; <em style="color:{fg};opacity:.8;">{source}</em>
        </div>""",
        unsafe_allow_html=True
    )


def _render_flegrei_sensor_caption(bulletin, gps_data, aq_data):
    sources = [f"{_gt('bulletin_ingv_ov_short')} ({bulletin['bulletin_date']})"]
    if gps_data:
        sources.append(f"{_gt('gps_ngl_updated')} {gps_data['last_date']}")
    if aq_data and "so2" in aq_data:
        sources.append(_gt("openaq_live_str"))
    st.caption(_gt("data_sources_label") + ": " + " · ".join(sources))


def _render_sensor_status_vesuvio(vesuvio_data, bulletin, gps_data=None, aq_data=None):
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    ingv_status = _gt("status_online_str") if not vesuvio_data.empty else _gt("status_no_event_str")
    bul_str = _gt("status_bulletin_str")
    bul_date = bulletin.get('bulletin_date', 'Aggiornamento live')
    # GPS dinamico — identico alla logica CF
    gps_status = _gt('status_online_str') if gps_data else bul_str
    gps_date   = now_str if gps_data else bul_date
    gps_src    = f"NGL / INGV RING (dati al {gps_data['last_date']})" if gps_data else "Live / INGV RING"
    gps_acc    = "±0.5 mm" if gps_data else "—"
    # Aria / CAMS
    has_aq = aq_data and isinstance(aq_data, dict) and "so2" in aq_data
    aq_status = f"{_gt('status_online_str')} (live)" if has_aq else bul_str
    aq_date   = now_str if has_aq else bul_date
    s = _gt("sensor_col_sensor"); st2 = _gt("sensor_col_status")
    upd = _gt("sensor_col_last_update"); src = _gt("sensor_col_source"); acc = _gt("sensor_col_accuracy")
    st.markdown(f"""
    | {s} | {st2} | {upd} | {src} | {acc} |
    |---------|--------|------------|-------|-------------|
    | {_gt('sensor_seismic_net')} | {ingv_status} | {now_str} | INGV FDSNWS API | ±0.1 M |
    | {_gt('sensor_gps_def')} | {gps_status} | {gps_date} | {gps_src} | {gps_acc} |
    | SO₂ / aria (CAMS) | {aq_status} | {aq_date} | CAMS Copernicus | ±2 μg/m³ |
    | {_gt('sensor_co2_so2')} | {bul_str} | {bul_date} | Live / INGV OV | — |
    | {_gt('sensor_temp_ground')} | {bul_str} | {bul_date} | Live / INGV OV | ±1°C |
    | {_gt('sensor_tilt_label')} | {bul_str} | {bul_date} | Live / INGV OV | ±0.01° |
    | {_gt('sensor_alert_level_lbl')} | {_gt('status_online_str')} | {now_str} | INGV OV (live) | — |
    """)
    st.caption(f"ℹ️ {_gt('sensor_cap_vesuvio')}")


def _render_sensor_status_flegrei(flegrei_data, bulletin, gps_data, aq_data):
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    ingv_status = _gt("status_online_str") if not flegrei_data.empty else _gt("status_no_event_str")
    gps_status = _gt('status_online_str') if gps_data else _gt("status_unavail_str")
    gps_acc = "±0.5 mm" if gps_data else "—"
    gps_src_cf = f"NGL / INGV RING (dati al {gps_data['last_date']})" if gps_data else "NGL / INGV RING"
    aq_status = f"{_gt('status_online_str')} (live)" if aq_data and "so2" in aq_data else _gt("status_not_avail_str")
    bul_str = _gt("status_bulletin_str")
    s = _gt("sensor_col_sensor"); st2 = _gt("sensor_col_status")
    upd = _gt("sensor_col_last_update"); src = _gt("sensor_col_source"); acc = _gt("sensor_col_accuracy")
    st.markdown(f"""
    | {s} | {st2} | {upd} | {src} | {acc} |
    |---------|--------|------------|-------|-------------|
    | {_gt('sensor_seismic_net')} | {ingv_status} | {now_str} | INGV FDSNWS API | ±0.1 M |
    | {_gt('sensor_gps_rite_label')} | {gps_status} | {now_str if gps_data else bulletin['bulletin_date']} | {gps_src_cf} | {gps_acc} |
    | {_gt('sensor_so2_air')} | {aq_status} | {now_str} | OpenAQ / ARPA Campania | ±2 μg/m³ |
    | {_gt('sensor_co2_solf')} | {bul_str} | {bulletin.get('bulletin_date','Aggiornamento live')} | Live / INGV OV | ±50 t/g |
    | {_gt('sensor_temp_fumar')} | {bul_str} | {bulletin.get('bulletin_date','Aggiornamento live')} | Live / INGV OV | ±1°C |
    | {_gt('sensor_h2s')} | {bul_str} | {bulletin.get('bulletin_date','Aggiornamento live')} | Live / INGV OV | ±5 t/g |
    | {_gt('sensor_tilt_label')} | {bul_str} | {bulletin.get('bulletin_date','Aggiornamento live')} | Live / INGV OV | ±0.01° |
    | {_gt('sensor_alert_level_lbl')} | {_gt('status_online_str')} | {now_str} | INGV OV (live) | — |
    """)
    st.caption(f"ℹ️ {_gt('sensor_cap_flegrei')}")


# ═══════════════════════════════════════════════════════════════════════════
# GRAFICI REALI
# ═══════════════════════════════════════════════════════════════════════════

def _format_energy(joules):
    if joules >= 1e12:
        return f"{joules / 1e12:.2f} TJ"
    elif joules >= 1e9:
        return f"{joules / 1e9:.2f} GJ"
    elif joules >= 1e6:
        return f"{joules / 1e6:.2f} MJ"
    elif joules >= 1e3:
        return f"{joules / 1e3:.2f} kJ"
    return f"{joules:.0f} J"


def _show_poisson_forecast(df, area_name: str):
    """
    Sezione probabilistica scientifica — Poisson + Gutenberg-Richter + Omori.
    Inserita sotto il calendario storico.
    """
    try:
        from forecast_service import generate_forecast_report
        report = generate_forecast_report(df, area_name)
        if not report:
            return
    except Exception:
        return

    pt    = report.get("prob_table", {})
    gr    = report.get("gutenberg_richter", {})
    omori = report.get("omori")
    lam   = report.get("rate_per_day", 0)
    n_ev  = report.get("n_events_used", 0)
    b     = gr.get("b", "—")

    _section_divider("📊 Stima Probabilistica — Metodo Poisson + Gutenberg-Richter")

    st.markdown(
        "<p style='font-size:0.83rem;color:#666;margin:-4px 0 10px 0;'>"
        "Le probabilità sotto sono <b>stime statistiche</b> basate sul tasso storico osservato — "
        "<b>non previsioni deterministiche</b>. I terremoti non sono prevedibili con certezza: "
        "questo è lo stato dell'arte della sismologia operativa mondiale."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── Info tasso, b-value, Mc ───────────────────────────────────────────
    mc_val = report.get("mc", 1.5)
    mi, bi, mci, ni = st.columns(4)
    with mi:
        st.metric("Tasso medio", f"{lam:.2f} ev/giorno",
                  help="Frequenza media eventi ≥Mc negli ultimi 30 giorni (INGV+USGS)")
    with bi:
        b_label = str(b) if b else "—"
        st.metric("b-value G-R", b_label,
                  help="Esponente Gutenberg-Richter (MLE Aki 1965). Valore tipico: 0.8–1.2")
    with mci:
        st.metric("Mc (MAXC)", f"M{mc_val}",
                  help="Magnitudo di completezza calcolata automaticamente (metodo MAXC, Wiemer & Wyss 2000)")
    with ni:
        st.metric("Campione", str(n_ev),
                  help=f"Numero di eventi ≥M{mc_val} usati per la stima")

    st.markdown("---")

    # ── Tabella probabilità ───────────────────────────────────────────────
    if pt:
        thresholds = sorted(pt.keys())
        rows = []
        icons = {1.5: "🟡", 2.0: "🟠", 3.0: "🔴", 4.0: "🆘", 5.0: "☢️"}
        for M in thresholds:
            row = {
                "Magnitudo": f"{icons.get(M,'')  } ≥ M{M}",
                "Prossime 24h": f"{pt[M].get(1, '—')}%",
                "Prossimi 7 giorni": f"{pt[M].get(7, '—')}%",
                "Prossimi 30 giorni": f"{pt[M].get(30, '—')}%",
            }
            rows.append(row)

        tdf = pd.DataFrame(rows)
        st.markdown(
            "<p style='font-size:0.82rem;font-weight:700;color:#444;margin-bottom:4px;'>"
            "P (almeno 1 evento) per soglia di magnitudo:</p>",
            unsafe_allow_html=True,
        )

        # Stile tabella colorata in HTML
        def _color_cell(val_str):
            try:
                v = float(val_str.replace("%", ""))
            except Exception:
                return val_str
            if v >= 90:
                bg, fg = "#c0392b", "#fff"
            elif v >= 60:
                bg, fg = "#e67e22", "#fff"
            elif v >= 30:
                bg, fg = "#f1c40f", "#333"
            elif v >= 10:
                bg, fg = "#2ecc71", "#333"
            else:
                bg, fg = "#ecf0f1", "#555"
            return (f"<span style='background:{bg};color:{fg};"
                    f"padding:2px 8px;border-radius:4px;font-weight:700;"
                    f"font-size:0.85rem;'>{val_str}</span>")

        hdr = "".join(f"<th style='padding:6px 12px;border-bottom:2px solid #dee2e6;"
                      f"text-align:center;font-size:0.82rem;'>{c}</th>" for c in tdf.columns)
        body = ""
        for _, r in tdf.iterrows():
            cells = f"<td style='padding:5px 10px;font-weight:600;'>{r['Magnitudo']}</td>"
            for col in ["Prossime 24h", "Prossimi 7 giorni", "Prossimi 30 giorni"]:
                cells += f"<td style='text-align:center;padding:5px 10px;'>{_color_cell(r[col])}</td>"
            body += f"<tr style='border-bottom:1px solid #f1f1f1;'>{cells}</tr>"

        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;margin-bottom:8px;'>"
            f"<thead><tr style='background:#f8f9fa;'>{hdr}</tr></thead>"
            f"<tbody>{body}</tbody></table>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p style='font-size:0.76rem;color:#999;margin-top:2px;'>"
            "Metodo: processo di Poisson stazionario con tasso λ_M ricavato dalla G-R. "
            "🟢 bassa / 🟡 moderata / 🟠 alta / 🔴 molto alta probabilità."
            "</p>",
            unsafe_allow_html=True,
        )

    # ── Omori (aftershock) se presente ───────────────────────────────────
    if omori:
        Mm   = omori["main_mag"]
        loc  = omori["main_location"]
        tel  = omori["t_elapsed_days"]
        a24  = omori["expected_24h"]
        a7d  = omori["expected_7d"]
        bath = omori["bath_max_mag"]
        t_str = omori["main_time"].strftime("%d/%m %H:%M") if hasattr(omori["main_time"], "strftime") else str(omori["main_time"])

        with st.expander(f"⚡ Sequenza attiva — Legge di Omori (evento M{Mm} del {t_str})", expanded=True):
            st.markdown(
                f"Evento principale **M{Mm}** — {loc} — {tel:.1f} giorni fa\n\n"
                f"**Aftershock attesi nelle prossime 24h:** ~{a24}  \n"
                f"**Aftershock attesi nei prossimi 7 giorni:** ~{a7d}  \n"
                f"**M massima aftershock attesa** (Legge di Båth): M ≤ {bath}  \n\n"
                f"*Legge di Omori-Utsu: n(t) = K/(t+c)^p  |  K={0.024*(10**(Mm-1)):.2f}, c=0.1, p=1*"
            )
            st.caption(
                "Il decadimento degli aftershock è una legge empirica ben validata. "
                "La magnitudo dei singoli aftershock rimane imprevedibile."
            )


def _show_risk_timeline_bar(df, area_name="Italia", plot_key="timeline"):
    """
    Barra orizzontale: passato 14gg (rischio storico) + futuro 14gg (previsione Poisson).
    Ogni giorno colorato per rischio: verde=normale, giallo=moderato, arancio=elevato, rosso=anomalo.
    """
    if df is None or df.empty:
        return
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from datetime import datetime, timedelta
        from math import exp, factorial

        def _poisson_expected_risk(lam):
            """
            Data la frequenza attesa lambda (eventi/giorno),
            restituisce il colore di rischio basato sulla soglia relativa alla baseline.
            """
            return lam  # usato per calcolo relativo sotto

        today = datetime.now().date()
        df2 = df.copy()
        df2["date"] = pd.to_datetime(df2["datetime"]).dt.date

        # ── Baseline: media e deviazione standard degli ultimi 30 giorni ──
        hist_start = today - timedelta(days=30)
        hist_counts = df2[df2["date"] >= hist_start].groupby("date").size()
        # Includi giorni con zero eventi
        all_days_30 = [today - timedelta(days=i) for i in range(30)]
        counts_list = [hist_counts.get(d, 0) for d in all_days_30]
        lambda_day = np.mean(counts_list) if sum(counts_list) > 0 else 0.5
        sigma_day  = np.std(counts_list) if len(counts_list) > 1 else 0.5

        def _color_for_count(count, lam, sig):
            """Colore basato su quante sigma sopra la media."""
            if lam <= 0:
                return "#1a5c2e"
            z = (count - lam) / max(sig, 0.1)
            if z < 0.5:  return "#1a5c2e"   # verde scuro: normale
            if z < 1.5:  return "#f1c40f"   # giallo: leggermente elevato
            if z < 2.5:  return "#e67e22"   # arancio: elevato
            return "#c0392b"                 # rosso: anomalo

        def _color_future(day_offset, lam, sig):
            """
            Per i giorni futuri usa la previsione Poisson:
            probabilità che ci siano eventi anomali basata su autocorrelazione recente.
            Applica un decadimento esponenziale della probabilità nel tempo.
            """
            # Peso recente: ultimi 7 giorni hanno più influenza
            recent = [hist_counts.get(today - timedelta(days=i), 0) for i in range(7)]
            recent_mean = np.mean(recent) if recent else lam
            # Decadimento nel tempo: più lontano nel futuro = ritorno alla baseline
            decay = 0.85 ** day_offset
            forecast_lambda = lam + (recent_mean - lam) * decay
            return _color_for_count(forecast_lambda, lam, sig)

        # ── Costruisci la barra: 14 giorni passato + oggi + 14 giorni futuro ──
        n_past   = 14
        n_future = 14
        total    = n_past + 1 + n_future  # 29 segmenti

        segments = []
        # Passato (da 14 giorni fa a ieri)
        for i in range(n_past, 0, -1):
            d = today - timedelta(days=i)
            c = hist_counts.get(d, 0)
            segments.append({
                "date": d, "future": False,
                "color": _color_for_count(c, lambda_day, sigma_day),
                "count": c,
            })
        # Oggi
        c_today = hist_counts.get(today, 0)
        segments.append({
            "date": today, "future": False,
            "color": _color_for_count(c_today, lambda_day, sigma_day),
            "count": c_today,
        })
        # Futuro (da domani a +14 giorni)
        for i in range(1, n_future + 1):
            d = today + timedelta(days=i)
            segments.append({
                "date": d, "future": True,
                "color": _color_future(i, lambda_day, sigma_day),
                "count": None,
            })

        # ── Titolo ────────────────────────────────────────────────────────
        _section_divider("📅 Calendario del Rischio")
        st.markdown("**Calendario del Rischio Sismico**")

        _dark = getattr(st.session_state, "dark_mode", False)
        _bg   = "#0e1117" if _dark else "#ffffff"
        _tc   = "#aaaaaa" if _dark else "#555555"

        import plotly.graph_objects as _pgo

        _risk_names = {
            "#1a5c2e": "🟢 Normale",
            "#f1c40f": "🟡 Moderato",
            "#e67e22": "🟠 Elevato",
            "#c0392b": "🔴 Anomalo",
        }

        # ── Barra Plotly interattiva (stacked horizontal bar) ─────────────
        bar_fig = _pgo.Figure()

        for i, seg in enumerate(segments):
            date_str   = seg["date"].strftime("%d %b %Y")
            risk_label = _risk_names.get(seg["color"], "")
            if seg["future"]:
                detail = "📊 Previsione probabilistica"
            else:
                detail = f"Osservati: <b>{seg['count']}</b> eventi"

            bar_fig.add_trace(_pgo.Bar(
                x=[1.0 / total],
                y=["Rischio Previsto"],
                orientation="h",
                marker=dict(
                    color=seg["color"],
                    opacity=0.55 if seg["future"] else 1.0,
                    line=dict(width=0),
                ),
                customdata=[[date_str, risk_label, detail]],
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Rischio: %{customdata[1]}<br>"
                    "%{customdata[2]}<extra></extra>"
                ),
                showlegend=False,
            ))

        # Linea "Oggi"
        today_frac = (n_past + 0.5) / total
        bar_fig.add_shape(
            type="line",
            x0=today_frac, x1=today_frac, y0=-0.45, y1=0.45,
            line=dict(color="white" if _dark else "#333333", width=2),
            xref="x", yref="y",
        )
        bar_fig.add_annotation(
            x=today_frac, y=0.5,
            text=f"<b>Oggi<br>{today.strftime('%-d %b')}</b>",
            showarrow=False,
            font=dict(size=9, color="white" if _dark else "#333"),
            xref="x", yref="y", align="center",
        )

        # Date labels ogni 7 giorni
        for tick_i in range(0, total, 7):
            if tick_i < len(segments):
                frac = (tick_i + 0.5) / total
                bar_fig.add_annotation(
                    x=frac, y=-0.52,
                    text=segments[tick_i]["date"].strftime("%-d %b"),
                    showarrow=False,
                    font=dict(size=9, color=_tc),
                    xref="x", yref="y",
                )

        # Marcatore picco futuro
        risk_order = {"#c0392b": 3, "#e67e22": 2, "#f1c40f": 1, "#1a5c2e": 0}
        future_segs = [(i, s) for i, s in enumerate(segments) if s["future"]]
        if future_segs:
            peak_i, peak_seg = max(future_segs, key=lambda x: risk_order.get(x[1]["color"], 0))
            if risk_order.get(peak_seg["color"], 0) > 0:
                px = (peak_i + 0.5) / total
                bar_fig.add_shape(
                    type="line",
                    x0=px, x1=px, y0=-0.45, y1=0.45,
                    line=dict(color=peak_seg["color"], width=1.5, dash="dash"),
                    xref="x", yref="y",
                )
                bar_fig.add_annotation(
                    x=px, y=-0.72,
                    text=peak_seg["date"].strftime("%-d %b %Y"),
                    showarrow=False,
                    font=dict(size=9, color=_tc),
                    xref="x", yref="y",
                )

        bar_fig.update_layout(
            barmode="stack",
            height=110,
            margin=dict(l=0, r=0, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(range=[0, 1], showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(color=_tc, size=11),
            ),
            showlegend=False,
            hoverlabel=dict(bgcolor="#222" if _dark else "#fff", font_size=12),
        )

        st.plotly_chart(bar_fig, width='stretch', key=f"riskbar_{plot_key}")

        # ── Trend Eventi (ultimi 3gg vs 3gg precedenti) ───────────────────
        last3 = sum(hist_counts.get(today - timedelta(days=i), 0) for i in range(3))
        prev3 = sum(hist_counts.get(today - timedelta(days=i + 3), 0) for i in range(3))
        delta_str = None
        if prev3 > 0:
            dp = round((last3 - prev3) / prev3 * 100)
            delta_str = f"{'↑' if dp >= 0 else '↓'}{abs(dp)}%"

        # ── Indice di Clustering (CV inter-evento = CoV-IET) ─────────────
        # Coefficiente di variazione dei tempi inter-evento:
        #   CoV < 0.5  → sismicità quasi-periodica (regolare)
        #   CoV ≈ 1.0  → processo Poissoniano casuale (benchmark)
        #   CoV > 1.0  → sciame / clustering anomalo
        # Richiede ≥2 eventi; con meno si mostra "N/D" (non calcolabile).
        clustering_val = None
        clustering_str = "N/D"
        clustering_delta = None
        try:
            times = pd.to_datetime(df2["datetime"]).sort_values()
            inter = times.diff().dt.total_seconds().dropna()
            n_inter = len(inter)
            if n_inter >= 2 and inter.mean() > 0:
                cov = round(float(inter.std()) / float(inter.mean()), 2)
                clustering_val = min(cov, 9.99)
                clustering_str = f"{clustering_val:.2f}"
                if clustering_val < 0.5:
                    clustering_delta = "regolare"
                elif clustering_val < 1.0:
                    clustering_delta = "sub-Poisson"
                elif clustering_val < 2.0:
                    clustering_delta = "Poisson/lieve cluster"
                else:
                    clustering_delta = "⚠️ clustering"
            elif n_inter == 1:
                clustering_str = "N/D (< 3 eventi)"
        except Exception:
            clustering_str = "N/D"

        tc1, tc2 = st.columns(2)
        with tc1:
            st.metric(
                "Trend Eventi",
                f"{last3} eventi (3gg)",
                delta=delta_str,
                help="Numero di eventi sismici negli ultimi 3 giorni rispetto ai 3 giorni precedenti",
            )
        with tc2:
            st.metric(
                "Indice di Clustering",
                clustering_str,
                delta=clustering_delta,
                help=(
                    "Coefficiente di variazione dei tempi inter-evento (CoV-IET). "
                    "< 0.5 = sismicità regolare; ≈ 1.0 = casuale (Poisson); "
                    "> 1.0 = raggruppamento anomalo (sciame). "
                    "Richiede ≥ 2 eventi nello stesso periodo."
                ),
            )

    except Exception as exc:
        st.caption(f"Calendario rischio non disponibile: {exc}")


def _show_risk_calendar(df, area_name="Italia", plot_key="cal"):
    """Calendario rischio sismico — heatmap ultimi 30 giorni con codice colore."""
    _section_divider(_gt("risk_calendar"))

    if df is None or df.empty:
        st.info(_gt("no_data_calendar"))
        return

    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start = today - timedelta(days=29)

        df2 = df.copy()
        if "datetime" not in df2.columns:
            st.info(_gt("no_temporal_data_calendar"))
            return
        df2["date"] = pd.to_datetime(df2["datetime"]).dt.date
        daily = df2[df2["date"] >= start].groupby("date").size().reset_index(name="count")
        daily_dict = dict(zip(daily["date"], daily["count"]))

        days = [start + timedelta(days=i) for i in range(30)]
        counts = [daily_dict.get(d, 0) for d in days]

        max_count = max(counts) if max(counts) > 0 else 1
        norm = mcolors.Normalize(vmin=0, vmax=max(max_count, 5))
        cmap = plt.cm.RdYlGn_r

        n_weeks = 5
        grid = np.zeros((7, n_weeks))
        date_grid = [[None]*n_weeks for _ in range(7)]

        first_weekday = start.weekday()
        for i, (d, c) in enumerate(zip(days, counts)):
            col = (first_weekday + i) // 7
            row = (first_weekday + i) % 7
            if col < n_weeks:
                grid[row, col] = c
                date_grid[row][col] = d

        _dark = getattr(st.session_state, 'dark_mode', False)
        _bg     = "#0e1117" if _dark else "#ffffff"
        _axbg   = "#1e2a3a" if _dark else "#f8f9fa"
        _tc     = "#e8eaf0" if _dark else "#1d3557"

        fig, ax = plt.subplots(figsize=(10, 3), facecolor=_bg)
        ax.set_facecolor(_axbg)

        day_labels = _gt("cal_days_str").split(",")
        for row in range(7):
            for col in range(n_weeks):
                d = date_grid[row][col]
                if d is None:
                    continue
                c_val = grid[row, col]
                color = cmap(norm(c_val))
                rect = plt.Rectangle([col - 0.45, 6 - row - 0.45], 0.9, 0.9,
                                      color=color, zorder=2)
                ax.add_patch(rect)
                txt_color = "white" if norm(c_val) > 0.45 else (_tc)
                ax.text(col, 6 - row, str(int(c_val)), ha="center", va="center",
                        fontsize=8, color=txt_color, fontweight="bold", zorder=3)

        week_starts = []
        for col in range(n_weeks):
            d = date_grid[0][col] or date_grid[1][col] or date_grid[2][col]
            if d:
                week_starts.append((col, d.strftime("%d/%m")))

        ax.set_xlim(-0.5, n_weeks - 0.5)
        ax.set_ylim(-0.5, 6.5)
        ax.set_yticks(range(7))
        ax.set_yticklabels([day_labels[6 - i] for i in range(7)],
                           color=_tc, fontsize=9)
        ax.set_xticks([c for c, _ in week_starts])
        ax.set_xticklabels([lbl for _, lbl in week_starts], color=_tc, fontsize=9)
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, orientation="vertical", pad=0.02, fraction=0.04)
        cbar.set_label(_gt("cal_events_per_day"), color=_tc, fontsize=8)
        cbar.ax.yaxis.set_tick_params(color=_tc)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=_tc, fontsize=7)

        title_color = "#e63946"
        ax.set_title(f"{_gt('cal_chart_title')} — {area_name} (INGV+USGS live)",
                     color=title_color, fontsize=11, fontweight="bold", pad=8)

        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)
        plt.close(fig)

        max_day = days[counts.index(max(counts))]
        st.caption(
            f"🟢 = pochi eventi  |  🔴 = alta attività  |  "
            f"Giorno più attivo: **{max_day.strftime('%d/%m')}** ({max(counts)} eventi)  |  "
            f"Totale 30 giorni: **{sum(counts)}** eventi — Fonte: INGV + USGS"
        )

    except Exception as e:
        st.warning(f"{_gt('cal_unavailable')}: {e}")


def _plot_seismic_energy_timeseries(df, area_name, plot_key="energy"):
    """Grafico energia sismica giornaliera — DATI REALI INGV/USGS."""
    if df is None or df.empty:
        st.info(_gt("no_data_energy"))
        return

    _, daily_energy = compute_seismic_energy(df)
    if daily_energy.empty:
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily_energy["date"],
        y=daily_energy["energy_j"],
        name=_gt("energy_j_label"),
        marker_color=PALETTE["primary"],
        hovertemplate=f"<b>%{{x}}</b><br>{_gt('energy_label_short')}: %{{y:.2e}} J<extra></extra>"
    ))
    fig.update_layout(
        title=f"{_gt('energy_daily_title')} — {area_name}",
        xaxis_title=_gt("chart_date_lbl"),
        yaxis_title=_gt("energy_j_label"),
        yaxis_type="log",
        margin=dict(l=0, r=0, t=40, b=0)
    )
    st.plotly_chart(fig, key=f"energy_{plot_key}")
    st.caption(_gt("energy_caption"))


def _plot_magnitude_distribution(df, title="Distribuzione Magnitudo", plot_key="mag"):
    if df is None or df.empty:
        st.info(_gt("no_data"))
        return
    bins = compute_magnitude_distribution(df)
    fig = px.bar(
        x=list(bins.keys()),
        y=list(bins.values()),
        title=title,
        labels={"x": _gt("chart_mag_class"), "y": _gt("chart_events_n")},
        color=list(bins.keys()),
        color_discrete_map={
            "M < 1.5": "#2dc653",
            "M 1.5-2.5": "#f4a261",
            "M 2.5-3.5": "#e76f51",
            "M 3.5-5.0": "#e63946",
            "M > 5.0": "#9b1d20",
        }
    )
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=35, b=0))
    st.plotly_chart(fig, key=f"mag_{plot_key}")


def _plot_depth_distribution(df, title="Distribuzione Profondità", plot_key="depth"):
    if df is None or df.empty:
        st.info(_gt("no_data"))
        return
    bins = compute_depth_distribution(df)
    fig = px.pie(
        values=list(bins.values()),
        names=list(bins.keys()),
        title=title,
        color=list(bins.keys()),
        color_discrete_map=DEPTH_COLORS,
        hole=0.35,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=35, b=0))
    st.plotly_chart(fig, key=f"depth_{plot_key}")


def _plot_hourly_distribution(df, area_name, plot_key="hourly"):
    if df is None or df.empty:
        return
    hourly = compute_hourly_distribution(df)
    if not hourly:
        return
    hours = list(range(24))
    counts = [hourly.get(h, 0) for h in hours]
    fig = px.bar(
        x=hours, y=counts,
        title=f"{_gt('hourly_dist_title')} — {area_name} (UTC)",
        labels={"x": _gt("chart_hour_utc"), "y": _gt("chart_events_n")},
        color_discrete_sequence=[PALETTE["secondary"]],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=35, b=0))
    st.plotly_chart(fig, key=f"hourly_{plot_key}")


def _plot_daily_activity(df):
    if df is None or df.empty:
        return
    stats = calculate_earthquake_statistics(df)
    if not stats["daily_counts"]:
        return
    dates = sorted(stats["daily_counts"].keys())
    counts = [stats["daily_counts"][d] for d in dates]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=counts,
        name=_gt("chart_events_n"),
        marker_color=PALETTE["primary"],
        opacity=0.8,
    ))

    # Media mobile 7 giorni
    if len(counts) >= 3:
        window = min(7, len(counts))
        rolling = (
            pd.Series(counts)
            .rolling(window=window, center=True, min_periods=1)
            .mean()
            .round(2)
            .tolist()
        )
        fig.add_trace(go.Scatter(
            x=dates, y=rolling,
            mode="lines",
            name=f"Media mobile {window}gg",
            line=dict(color="#e63946", width=2.5),
            opacity=0.95,
        ))

    fig.update_layout(
        title=_gt("daily_activity_title"),
        xaxis_title=_gt("chart_date_lbl"),
        yaxis_title=_gt("chart_events_n"),
        margin=dict(l=0, r=0, t=35, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        bargap=0.15,
    )
    st.plotly_chart(fig, key="daily_activity_italia")


def _show_area_analytics(df, area_name):
    if df is None or df.empty:
        st.info(_gt("insufficient_data_stats"))
        return

    ak = area_name.replace(" ", "_").lower()
    col1, col2 = st.columns(2)
    with col1:
        _plot_magnitude_distribution(df, f"{_gt('magnitude_distribution')} — {area_name}", plot_key=f"analytics_{ak}")
    with col2:
        _plot_depth_distribution(df, f"{_gt('depth_distribution')} — {area_name}", plot_key=f"analytics_{ak}")

    _plot_hourly_distribution(df, area_name, plot_key=f"analytics_{ak}")

    with st.expander(_gt("detailed_stats"), expanded=False):
        stats = calculate_earthquake_statistics(df)
        st.table(pd.DataFrame({
            _gt("stat_indicator"): [_gt("total_events_7d_stat"), _gt("max_magnitude_stat"),
                                    _gt("avg_magnitude_stat"), _gt("avg_depth_stat"), _gt("primary_source")],
            _gt("stat_value"): [str(stats["count"]), f"{stats['max_magnitude']:.1f}",
                                f"{stats['avg_magnitude']:.1f}", f"{stats['avg_depth']:.1f} km",
                                "INGV + USGS"]
        }))
        st.caption(_gt("data_update_caption"))


def _show_ingv_news(area: str = "all"):
    """
    Mostra le ultime notizie INGV OV scraped dalla homepage ufficiale.

    area: "cf" | "vesuvio" | "ischia" | "all"
    Le notizie hanno immagini, date, titoli e link reali.
    """
    _AREA_MAP = {"cf": "cf", "flegrei": "cf", "vesuvio": "vesuvio", "ischia": "ischia", "all": "all"}
    _filter = _AREA_MAP.get(area, "all")
    news = fetch_ingv_news(max_items=8, area_filter=_filter)
    # fallback: se nessuna per area, mostra quelle generali
    if not news and _filter != "all":
        news = fetch_ingv_news(max_items=5, area_filter="all")
    if not news:
        return
    _label_map = {
        "cf": "Campi Flegrei",
        "vesuvio": "Vesuvio",
        "ischia": "Ischia",
        "all": "INGV OV",
    }
    with st.expander(
        f"📰 Ultime notizie {_label_map.get(_filter,'INGV OV')} — Osservatorio Vesuviano",
        expanded=False,
    ):
        st.caption("Dati estratti in tempo reale dalla homepage www.ov.ingv.it · aggiornamento ogni ora")
        cols_per_row = 2
        rows = [news[i : i + cols_per_row] for i in range(0, len(news), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for col, item in zip(cols, row):
                with col:
                    if item.get("image_url"):
                        try:
                            st.markdown(
                                f"<a href='{item['link']}' target='_blank' rel='noopener'>"
                                f"<img src='{item['image_url']}' style='width:100%;border-radius:6px;"
                                f"margin-bottom:4px;object-fit:cover;max-height:140px;' /></a>",
                                unsafe_allow_html=True,
                            )
                        except Exception:
                            pass
                    st.markdown(
                        f"**[{item['title']}]({item['link']})**",
                        help="Apri articolo sul sito INGV OV",
                    )
                    meta_parts = []
                    if item.get("date"):
                        meta_parts.append(f"📅 {item['date']}")
                    if item.get("hits"):
                        meta_parts.append(f"👁 {item['hits']} visite")
                    cats_nice = [c.replace("cat-news-","").replace("cat-","") for c in item.get("categories",[])]
                    if cats_nice:
                        meta_parts.append(" · ".join(cats_nice))
                    if meta_parts:
                        st.caption(" · ".join(meta_parts))
        st.markdown(
            "[→ Tutte le notizie INGV OV](https://www.ov.ingv.it/index.php/it/news-ov)",
            unsafe_allow_html=False,
        )


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_thumb_b64(url: str) -> str:
    """
    Scarica il thumbnail YouTube server-side e lo restituisce come data-URI base64.
    Cache 30 min. Chiamare dal thread principale Streamlit (non da ThreadPoolExecutor).
    """
    import base64
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "SeismicSafetyItalia/2.0"})
        if r.status_code == 200 and r.headers.get("content-type","").startswith("image"):
            return "data:image/jpeg;base64," + base64.b64encode(r.content).decode()
    except Exception:
        pass
    return ""


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_solfatara_rss() -> list:
    """Scarica i video recenti di SolfataraNews dal feed RSS YouTube."""
    import xml.etree.ElementTree as ET
    url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCC1XzjkXRz0DLJfH-69t1vQ"
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt":   "http://www.youtube.com/xml/schemas/2015",
        "media":"http://search.yahoo.com/mrss/",
    }
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "SeismicSafetyItalia/2.0"})
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.text)
        videos = []
        for entry in root.findall("atom:entry", ns)[:6]:
            vid_el   = entry.find("yt:videoId", ns)
            title_el = entry.find("atom:title", ns)
            pub_el   = entry.find("atom:published", ns)
            if vid_el is None:
                continue
            vid_id = vid_el.text
            if not vid_id:
                continue
            title = title_el.text if title_el is not None else ""
            pub   = pub_el.text[:10] if pub_el is not None else ""
            videos.append({
                "id":    vid_id,
                "title": title,
                "pub":   pub,
                "thumb": f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
                "url":   f"https://www.youtube.com/watch?v={vid_id}",
            })
        return videos
    except Exception:
        return []


def _render_yt_cards(videos: list, fallback_url: str = "", caption_suffix: str = "") -> None:
    """
    Renderizza una griglia 3-colonne di card video YouTube.
    Usa st.image() per i thumbnail — caricamento server-side, nessun problema CSP.
    """
    if not videos:
        msg = "Feed RSS temporaneamente non disponibile."
        if fallback_url:
            msg += f" [→ Apri canale YouTube]({fallback_url})"
        st.info(msg)
        return

    # Griglia 3 colonne
    for row_start in range(0, len(videos), 3):
        row_videos = videos[row_start:row_start + 3]
        cols = st.columns(3)
        for col, v in zip(cols, row_videos):
            with col:
                thumb = v.get("thumb", "")
                if thumb:
                    try:
                        thumb_data = _fetch_thumb_bytes(thumb)
                        if thumb_data:
                            st.image(thumb_data, width='stretch')
                        else:
                            st.markdown("🎬")
                    except Exception:
                        st.markdown("🎬")
                title_short = v["title"][:68] + ("…" if len(v["title"]) > 68 else "")
                st.markdown(f"**[{title_short}]({v['url']})**")
                st.caption(f"📅 {v['pub']}")

    cap = "🔄 Aggiornato ogni 30 minuti · Fonte: YouTube RSS pubblico"
    if caption_suffix:
        cap += " · " + caption_suffix
    st.caption(cap)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_thumb_bytes(url: str) -> bytes | None:
    """Scarica thumbnail lato server e restituisce i bytes. Evita il blocco CSP del browser."""
    try:
        r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.content:
            return r.content
        return None
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_yt_rss(channel_id: str, keyword_filter: str = "") -> list:
    """
    Scarica ultimi video dal feed RSS YouTube di un canale.
    Filtra opzionalmente per keyword nel titolo.
    """
    import xml.etree.ElementTree as ET
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt":   "http://www.youtube.com/xml/schemas/2015",
        "media":"http://search.yahoo.com/mrss/",
    }
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(url, timeout=8, headers={"User-Agent": "SeismicSafetyItalia/2.0"})
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.text)
        videos = []
        kw = keyword_filter.lower() if keyword_filter else ""
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            vid_el   = entry.find("yt:videoId", ns)
            pub_el   = entry.find("atom:published", ns)
            if title_el is None or vid_el is None:
                continue
            title = title_el.text or ""
            if kw and kw not in title.lower():
                continue
            vid_id = vid_el.text
            pub    = (pub_el.text or "")[:10] if pub_el is not None else ""
            videos.append({
                "title": title,
                "thumb": f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
                "url":   f"https://www.youtube.com/watch?v={vid_id}",
                "pub":   pub,
            })
        return videos[:6]
    except Exception:
        return []


def _show_vesuvio_news() -> None:
    """
    Sezione Vesuvio News: webcam live H24 + ultimi video INGV Vulcani.
    Webcam: 'Webcam Live Vulcano Vesuvio' by Paesaggi Digitali (RbI8JwrBZQA).
    Video RSS: canale INGVvulcani (UC3GnD1b5hO8a-ag0yKr_uqw).
    """
    _section_divider("📡 Vesuvio News — Live & INGV")

    with st.expander("📹 Webcam LIVE H24 — Vesuvio", expanded=True):
        st.markdown(
            "<p style='color:#6B7280;font-size:0.85rem;margin-bottom:8px'>"
            "Diretta YouTube continua — <strong>Paesaggi Digitali</strong> · "
            "Telecamera puntata sul Vesuvio (NA)</p>",
            unsafe_allow_html=True,
        )
        st.iframe(
            "https://www.youtube.com/embed/RbI8JwrBZQA"
            "?autoplay=0&rel=0&modestbranding=1",
            height=380,
        )
        st.caption(
            "📺 Per la visione ottimale aprire in un'altra scheda · "
            "[→ Webcam Vesuvio su YouTube](https://www.youtube.com/watch?v=RbI8JwrBZQA)"
        )

    with st.expander("🎬 Ultimi video — @INGVvulcani", expanded=True):
        videos = _fetch_yt_rss("UC3GnD1b5hO8a-ag0yKr_uqw")
        _render_yt_cards(
            videos,
            fallback_url="https://www.youtube.com/@INGVvulcani",
            caption_suffix="[→ Canale @INGVvulcani](https://www.youtube.com/@INGVvulcani)",
        )


def _show_ischia_news() -> None:
    """
    Sezione Ischia News: webcam live H24 + ultimi video INGV Terremoti.
    Webcam: 'Ischia Live Webcam' by Panocam (Hllyp_GlG64).
    Video RSS: canale INGVterremoti (UCWcylY2YDfioFmDAULj3vgA).
    """
    _section_divider("📡 Ischia News — Live & INGV")

    with st.expander("📹 Webcam LIVE H24 — Ischia", expanded=True):
        st.markdown(
            "<p style='color:#6B7280;font-size:0.85rem;margin-bottom:8px'>"
            "Diretta YouTube continua — <strong>Panocam</strong> · "
            "Telecamera panoramica sull'isola di Ischia</p>",
            unsafe_allow_html=True,
        )
        st.iframe(
            "https://www.youtube.com/embed/Hllyp_GlG64"
            "?autoplay=0&rel=0&modestbranding=1",
            height=380,
        )
        st.caption(
            "📺 Per la visione ottimale aprire in un'altra scheda · "
            "[→ Webcam Ischia su YouTube](https://www.youtube.com/watch?v=Hllyp_GlG64)"
        )

    with st.expander("🎬 Ultimi video — @INGVterremoti", expanded=True):
        videos = _fetch_yt_rss("UCWcylY2YDfioFmDAULj3vgA")
        _render_yt_cards(
            videos,
            fallback_url="https://www.youtube.com/@INGVterremoti",
            caption_suffix="[→ Canale @INGVterremoti](https://www.youtube.com/@INGVterremoti)",
        )


def _show_solfatara_news() -> None:
    """
    Sezione SolfataraNews nel tab Campi Flegrei:
    - Webcam live H24 (YouTube embed)
    - Video recenti (RSS YouTube, thumbnail + titolo)
    - Link social (Instagram, TikTok)
    """
    _section_divider("📡 SolfataraNews — Citizen Journalism dai Campi Flegrei")

    # ── Webcam live embed ─────────────────────────────────────────────────────
    with st.expander("🔴 Webcam LIVE H24 — Solfatara & Campi Flegrei", expanded=True):
        st.markdown(
            "<p style='color:#6B7280;font-size:0.85rem;margin-bottom:8px'>"
            "Diretta YouTube continua — <strong>@SolfataraNews</strong> · "
            "Telecamera puntata su Solfatara e area flegrea</p>",
            unsafe_allow_html=True,
        )
        st.iframe(
            "https://www.youtube.com/embed/6Ie29xiu_SE"
            "?autoplay=0&rel=0&modestbranding=1",
            height=380,
        )
        st.caption(
            "📺 Per la visione ottimale aprire in un'altra scheda · "
            "[→ canale @SolfataraNews](https://www.youtube.com/@SolfataraNews)"
        )

    # ── Video recenti ─────────────────────────────────────────────────────────
    with st.expander("🎬 Ultimi video — SolfataraNews", expanded=True):
        videos = _fetch_solfatara_rss()
        _render_yt_cards(videos,
                         fallback_url="https://www.youtube.com/@SolfataraNews",
                         caption_suffix="[→ Canale @SolfataraNews](https://www.youtube.com/@SolfataraNews)")


def _link_row(icon_label, href, link_text):
    return (f"<tr><td style='padding:7px 12px;border-bottom:1px solid #e9ecef;white-space:nowrap'>"
            f"{icon_label}</td>"
            f"<td style='padding:7px 12px;border-bottom:1px solid #e9ecef;width:100%'>"
            f"<a href='{href}' target='_blank' rel='noopener'>{link_text}</a></td></tr>")


def _show_ingv_official_links(area):
    _table_start = ("<table style='width:100%;border-collapse:collapse;table-layout:fixed;"
                    "border:1px solid #dee2e6;border-radius:6px;overflow:hidden'>"
                    "<thead><tr>"
                    "<th style='padding:8px 12px;background:#f8f9fa;text-align:left;width:38%'>Risorsa</th>"
                    "<th style='padding:8px 12px;background:#f8f9fa;text-align:left;width:62%'>Link</th>"
                    "</tr></thead><tbody>")
    _table_end = "</tbody></table>"

    if area == "vesuvio":
        rows = (
            _link_row("🗺️ Mappa sismica INGV", "https://webservices.ingv.it/", "webservices.ingv.it") +
            _link_row("🌍 Terremoti INGV live", "https://terremoti.ingv.it/", "terremoti.ingv.it") +
            _link_row("📡 Rete sismica ISNet", "http://isnet.na.infn.it/", "isnet.na.infn.it") +
            _link_row("🚨 Protezione Civile — Vesuvio",
                      "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vesuvio/",
                      "rischi.protezionecivile.gov.it") +
            _link_row("🛰️ GPS Nevada Geodetic Lab (portale)",
                      "https://geodesy.unr.edu/PlugNPlayPortal.php",
                      "geodesy.unr.edu")
        )
        st.markdown(_table_start + rows + _table_end, unsafe_allow_html=True)
    elif area == "flegrei":
        rows = (
            _link_row("🛰️ GPS RITE — Portale NGL",
                      "https://geodesy.unr.edu/PlugNPlayPortal.php",
                      "geodesy.unr.edu") +
            _link_row("🌍 Terremoti INGV live", "https://terremoti.ingv.it/", "terremoti.ingv.it") +
            _link_row("💨 Qualità aria (OpenAQ)", "https://openaq.org/#/countries/IT", "openaq.org") +
            _link_row("🚨 Protezione Civile — CF",
                      "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/campi-flegrei/",
                      "rischi.protezionecivile.gov.it")
        )
        st.markdown(_table_start + rows + _table_end, unsafe_allow_html=True)
    elif area == "ischia":
        rows = (
            _link_row("🌍 Terremoti INGV live", "https://terremoti.ingv.it/", "terremoti.ingv.it") +
            _link_row("🔍 EMSC — Ischia",
                      "https://www.emsc-csem.org/Earthquake/seismologist.php?region=SOUTHERN+ITALY",
                      "emsc-csem.org") +
            _link_row("🚨 Protezione Civile — Ischia",
                      "https://www.protezionecivile.gov.it/it/rischio/rischio-sismico",
                      "protezionecivile.gov.it") +
            _link_row("🌊 ISPRA — Rischio frane Ischia",
                      "https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/pericolosita-e-rischio-idrogeologico",
                      "isprambiente.gov.it") +
            _link_row("📡 GPS ISCH — Portale NGL",
                      "https://geodesy.unr.edu/PlugNPlayPortal.php",
                      "geodesy.unr.edu")
        )
        st.markdown(_table_start + rows + _table_end, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# MAPPA SISMICA INTERATTIVA
# ═══════════════════════════════════════════════════════════════════════════

def show_map(df, area, get_text):
    if area == "Vesuvio":
        center, zoom = [40.8218, 14.4263], 12
        volcano_pos = [40.8218, 14.4263]
        volcano_name = "Vesuvio"
        use_satellite = True
    elif area == "Campi Flegrei":
        center, zoom = [40.8267, 14.1394], 12
        volcano_pos = [40.8267, 14.1394]
        volcano_name = "Solfatara / Campi Flegrei"
        use_satellite = True
    elif area == "Ischia":
        center, zoom = [40.737, 13.905], 12
        volcano_pos = [40.728, 13.897]
        volcano_name = "Monte Epomeo (Ischia)"
        use_satellite = True
    else:
        center, zoom = [42.0, 13.0], 6
        volcano_pos = None
        volcano_name = None
        use_satellite = False

    if use_satellite:
        m = folium.Map(location=center, zoom_start=zoom, tiles=None)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="© Esri, USGS, NOAA",
            name="Satellite ESRI",
            overlay=False, control=False,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="© Esri", name="Labels",
            overlay=True, control=False, opacity=0.7,
        ).add_to(m)
    else:
        m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    if volcano_pos:
        folium.Circle(
            volcano_pos, radius=4000, color="#ff6b35", fill=True,
            fill_color="#ff6b35", fill_opacity=0.12, tooltip=f"{volcano_name} — raggio 4km"
        ).add_to(m)
        folium.Marker(
            volcano_pos,
            popup=folium.Popup(f"<b>🌋 {volcano_name}</b>", max_width=200),
            tooltip=volcano_name,
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
        ).add_to(m)

    has_data = df is not None and not df.empty
    if has_data:
        for _, row in df.iterrows():
            radius = max(3, 2 * row["magnitude"])
            color = "red" if row["depth"] < 5 else ("orange" if row["depth"] < 20 else "blue")
            popup = (
                f"<b>{_gt('popup_mag')}</b> {row['magnitude']:.1f}<br>"
                f"<b>{_gt('popup_depth')}</b> {row['depth']:.1f} km<br>"
                f"<b>{_gt('popup_location_lbl')}</b> {row['location']}<br>"
                f"<b>{_gt('popup_time_utc')}</b> {row.get('formatted_time', '')}<br>"
                f"<b>{_gt('popup_source_lbl')}</b> {row['source']}"
            )
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                color=color, fill=True, fill_color=color, fill_opacity=0.7,
                popup=folium.Popup(popup, max_width=300)
            ).add_to(m)

    folium_static(m, width=None, height=450)

    if has_data:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(get_text("total_events"), len(df))
        with c2:
            st.metric(get_text("metric_mag_max"), f"{df['magnitude'].max():.1f}")
        with c3:
            st.metric(get_text("metric_mag_avg"), f"{df['magnitude'].mean():.1f}")
        st.caption(get_text("depth_map_caption"))
    else:
        st.caption(_gt("satellite_caption_no_data").format(name=volcano_name or area))


# ═══════════════════════════════════════════════════════════════════════════
# TABELLA TERREMOTI + RISK BANNER
# ═══════════════════════════════════════════════════════════════════════════

def show_earthquake_table(df, get_text):
    if df is None or df.empty:
        st.warning(get_text("no_data"))
        return

    stats = calculate_earthquake_statistics(df)
    risk_level, risk_metrics = calculate_risk_level(stats, "Italy")

    _show_risk_banner(risk_level, risk_metrics, stats, ctx_key="table")

    st.subheader(get_text("eq_list_title"))
    st.caption(get_text("eq_list_caption"))

    display_df = df[["formatted_time", "magnitude", "depth", "location", "source"]].copy()
    display_df.insert(0, "Zona", df.apply(
        lambda r: _zona_label(r.get("latitude", 0), r.get("longitude", 0)), axis=1
    ))
    display_df.columns = [
        "Zona", get_text("time"), get_text("magnitude"),
        get_text("depth") + " (km)", get_text("location"), get_text("fonte"),
    ]
    st.dataframe(display_df, width='stretch', hide_index=True,
                 column_config={"Zona": st.column_config.ImageColumn("Zona", width="small")})

    # ── CSV export ────────────────────────────────────────────────────────────
    import io as _io
    csv_buf = _io.StringIO()
    display_df.to_csv(csv_buf, index=False)
    ts_label = datetime.now().strftime("%Y%m%d_%H%M")
    _dcol, _ = st.columns([1, 4])
    with _dcol:
        st.download_button(
            label="⬇️ Scarica CSV",
            data=csv_buf.getvalue().encode("utf-8"),
            file_name=f"terremoti_{ts_label}.csv",
            mime="text/csv", key=f"csv_dl_{ts_label}",
        )

    col1, col2 = st.columns(2)
    with col1:
        _plot_magnitude_distribution(df, plot_key="table")
    with col2:
        _plot_depth_distribution(df, plot_key="table")


def _show_risk_banner(risk_level, risk_metrics, stats, ctx_key="default"):
    # ── Verdetto immediato in linguaggio semplice ──────────────────────────
    _cfg = {
        "basso": {
            "icon": "✅", "bg": "#d4edda", "border": "#27ae60", "fg": "#155724",
            "titolo": "Attività nella norma",
            "cosa_fare": "Nessuna azione necessaria. Continua la tua giornata normalmente.",
        },
        "moderato": {
            "icon": "⚠️", "bg": "#fff3cd", "border": "#f39c12", "fg": "#856404",
            "titolo": "Attività moderata",
            "cosa_fare": "Tieni d'occhio gli aggiornamenti. Non è richiesta alcuna azione immediata.",
        },
        "elevato": {
            "icon": "🟠", "bg": "#fde8d8", "border": "#e67e22", "fg": "#7f3000",
            "titolo": "Attività elevata rispetto alla media",
            "cosa_fare": "Resta informato. L'allerta ufficiale INGV è GIALLO — nessuna evacuazione in corso.",
        },
        "molto elevato": {
            "icon": "🔴", "bg": "#f8d7da", "border": "#e63946", "fg": "#721c24",
            "titolo": "Attività molto elevata rispetto alla media",
            "cosa_fare": "Segui i comunicati ufficiali della Protezione Civile (112 / 800 232525).",
        },
    }
    v = _cfg.get(risk_level, _cfg["basso"])
    avg_d = stats.get("avg_depth", 0)

    # ── Gauge speedometer (Livello di Rischio) + Banner affiancati ──────────
    score = round(
        (risk_metrics.get("event_frequency", 0)
         + risk_metrics.get("magnitude_risk", 0)
         + risk_metrics.get("depth_risk", 0)
         + risk_metrics.get("clustering", 0)) / 4 * 100, 1
    )
    gauge_col, banner_col = st.columns([4, 6], gap="medium")
    with gauge_col:
        import plotly.graph_objects as _go
        _gauge_fig = _go.Figure(_go.Indicator(
            mode="gauge",
            value=score,
            title={"text": "Livello di Rischio", "font": {"size": 14}},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#555",
                         "tickvals": [0, 20, 40, 60, 80, 100]},
                "bar": {"color": "#333333", "thickness": 0.15},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 30],  "color": "#27ae60"},
                    {"range": [30, 60], "color": "#f1c40f"},
                    {"range": [60, 80], "color": "#e67e22"},
                    {"range": [80, 100],"color": "#e63946"},
                ],
                "shape": "angular",
            },
        ))
        # Numero centrato nel mezzo geometrico del semicerchio
        _gauge_fig.add_annotation(
            x=0.5, y=0.18,
            text=f"<b>{int(round(score))}</b>",
            font=dict(size=52, color="#222222"),
            showarrow=False,
            xref="paper", yref="paper",
            xanchor="center", yanchor="middle",
        )
        _gauge_fig.update_layout(
            height=230,
            margin=dict(l=20, r=20, t=55, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#222"},
        )
        st.plotly_chart(_gauge_fig, width='stretch', key=f"gauge_{ctx_key}")
    with banner_col:
        st.markdown(f"""
<div style="background:{v['bg']};border:1px solid {v['border']};border-left:5px solid {v['border']};
border-radius:8px;padding:14px 18px;margin-bottom:10px;">
  <div style="font-size:1.1rem;font-weight:700;color:{v['fg']};">{v['icon']} {v['titolo']}</div>
  <div style="color:{v['fg']};margin-top:6px;font-size:0.93rem;">
    <b>Dati periodo:</b> {stats['count']} eventi &nbsp;·&nbsp;
    Magnitudo max: <b>{stats['max_magnitude']:.1f}</b> &nbsp;·&nbsp;
    Profondità media: <b>{avg_d:.1f} km</b>
  </div>
  <div style="color:{v['fg']};margin-top:8px;font-size:0.97rem;">
    👉 <b>{v['cosa_fare']}</b>
  </div>
  <div style="color:{v['fg']};font-size:0.85rem;margin-top:8px;font-style:italic;">
    ℹ️ Indice statistico su dati reali INGV/USGS — non sostituisce i comunicati ufficiali della Protezione Civile.
  </div>
</div>""", unsafe_allow_html=True)

    # ── Indicatori tecnici (in expander) ──────────────────────────────────
    with st.expander("📊 Indicatori tecnici dettagliati", expanded=False):
        indicators = [
            (_gt("risk_freq"), risk_metrics["event_frequency"]),
            (_gt("risk_mag_ind"), risk_metrics["magnitude_risk"]),
            (_gt("risk_depth_ind"), risk_metrics["depth_risk"]),
            (_gt("risk_cluster"), risk_metrics["clustering"]),
        ]

        def _bar_color(v):
            if v < 0.30: return "#28a745"
            if v < 0.60: return "#ffc107"
            if v < 0.80: return "#fd7e14"
            return "#dc3545"

        # 4 colonne con barre HTML — funziona su qualsiasi tema e schermo
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        cols = st.columns(4, gap="medium")
        for col, (name, val) in zip(cols, indicators):
            pct = round(val * 100, 1)
            color = _bar_color(val)
            with col:
                st.markdown(
                    f"""<div style="background:#f8f9fa;border:1px solid #dee2e6;
border-radius:12px;padding:18px 14px 16px;text-align:center;min-height:120px;">
  <div style="font-size:13px;color:#333;margin-bottom:10px;font-weight:700;
line-height:1.4;">{name}</div>
  <div style="font-size:30px;font-weight:800;color:{color};
line-height:1.0;margin-bottom:12px;">{pct}%</div>
  <div style="background:#e9ecef;border-radius:6px;height:10px;overflow:hidden;">
    <div style="background:{color};width:{pct}%;height:100%;
border-radius:6px;transition:width .3s;"></div>
  </div>
</div>""",
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"<p style='font-size:13px;color:#444;margin-top:16px;margin-bottom:4px;font-style:italic;'>"
            f"ℹ️ {_gt('risk_caption_short')}</p>",
            unsafe_allow_html=True
        )


# ═══════════════════════════════════════════════════════════════════════════
# GRAFICO MAGNITUDO NEL TEMPO
# ═══════════════════════════════════════════════════════════════════════════

def show_magnitude_time_chart(df, area, get_text, show_risk=True):
    if df.empty:
        return

    area_key = area.replace(" ", "_").lower()
    fig = px.scatter(
        df, x="datetime", y="magnitude",
        size="magnitude", color="depth",
        hover_name="location",
        color_continuous_scale="RdYlBu_r",
        title=f"{_gt('mag_over_time_prefix')} {area}",
        labels={
            "datetime": get_text("time"),
            "magnitude": get_text("magnitude"),
            "depth": get_text("depth") + " (km)",
        },
    )
    fig.update_layout(hovermode="closest", margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, key=f"mag_time_{area_key}")

    if show_risk:
        stats = calculate_earthquake_statistics(df)
        risk_level, risk_metrics = calculate_risk_level(stats, area)
        _show_area_risk_detail(risk_level, risk_metrics, stats, area)
        _show_risk_timeline_bar(df, area_name=area, plot_key=area_key)

    # SAR Sentinel-1 — sezione dati istituzionali (non casuali)
    _section_divider(_gt("sar_section"))
    sar_col1, sar_col2 = st.columns(2)
    with sar_col1:
        st.markdown(_gt("sar_section_intro"))
    with sar_col2:
        st.markdown(_gt("sar_section_legend"))


def _show_area_risk_detail(risk_level, risk_metrics, stats, area):
    st.subheader(f"{_gt('risk_assessment_prefix')} {area}")
    _show_risk_banner(risk_level, risk_metrics, stats, ctx_key=f"detail_{area.replace(' ','_').lower()}")

    if stats.get("count", 0) > 0:
        if area == "Campi Flegrei" and stats.get("avg_depth", 10) < 3:
            st.warning(_gt("warn_bradisismo"))
        if area == "Vesuvio" and stats.get("max_magnitude", 0) > 3.0:
            st.warning(_gt("warn_vesuvio_m3"))

    st.markdown(
        f"<p style='font-size:13px;color:#444;margin-top:4px;font-style:italic;'>{_gt('risk_disclaimer_caption')}</p>",
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════════════
# ML + AI FORECAST CALENDAR
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def _cached_ml_forecast(df_hash: str, area: str, with_ai: bool, _df: pd.DataFrame):
    return run_ml_forecast(_df, area=area, horizon=7, with_ai_narrative=with_ai)


def _show_ml_forecast_calendar(df: pd.DataFrame, area: str, area_key: str):
    """
    Calendario previsione rischio sismico ML — prossimi 7 giorni.
    Ensemble RandomForest + Poisson-G-R con narrazione AI opzionale.
    """
    _section_divider(_gt("ml_forecast_title"))

    _dark = getattr(st.session_state, "dark_mode", False)
    _muted = "#9aa8b8" if _dark else "#666"
    _bg    = "#0e1117" if _dark else "#ffffff"
    _card_bg = "#1e2a3a" if _dark else "#f4f6fa"

    if df is None or df.empty:
        st.info("Dati insufficienti per la previsione ML (nessun evento disponibile).")
        return

    with st.spinner("⚙️ Training modello ensemble RF+Poisson…"):
        try:
            df_hash = str(len(df)) + str(df["datetime"].max()) + area
            with_ai  = st.session_state.get("ml_ai_narrative", True)
            result   = _cached_ml_forecast(df_hash, area, with_ai, df)
        except Exception as e:
            st.error(f"Errore forecast ML: {e}")
            return

    if result.get("error"):
        err = result["error"]
        if "classi" in err or "insufficienti" in err or "min 20" in err:
            st.info(
                f"📊 **Modello ML non disponibile per {area}**\n\n"
                f"La sisimicità strumentale INGV per quest'area è troppo bassa "
                f"per addestrare il modello RandomForest (pochi eventi registrati negli ultimi 90 giorni). "
                f"Per **{area}** usa la stima probabilistica di Poisson+Gutenberg-Richter mostrata sopra — "
                f"è il metodo scientificamente più appropriato per aree a bassa sisimicità.",
                icon="ℹ️"
            )
        else:
            st.warning(f"⚠️ {err}")
        return

    days       = result["days"]
    cv         = result["cv_score"]
    w_rf       = result["weight_rf"]
    w_poi      = result["weight_poisson"]
    n_train    = result["n_train"]
    top_feats  = result["top_features"]
    ai_text    = result.get("ai_narrative")

    # ── Metrica qualità modello ──────────────────────────────────────────
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        st.metric("Accuratezza CV (storico)", f"{round(cv*100,1)}%",
                  help="Accuratezza TimeSeriesSplit su dati passati (non futuri)")
    with col_q2:
        st.metric("Peso RF / Poisson", f"{round(w_rf*100,0):.0f}% / {round(w_poi*100,0):.0f}%",
                  help="Pesi ensemble calibrati su log-loss storico")
    with col_q3:
        st.metric("Giorni training", f"{n_train}",
                  help="Giorni di storico usati per addestrare il modello")

    # ── Calendario 7 giorni ─────────────────────────────────────────────
    st.markdown(f"<p style='font-size:0.82rem;color:{_muted};margin:4px 0 10px;'>"
                f"Previsione sismicità prossimi 7 giorni — Ensemble RF+Poisson calibrato</p>",
                unsafe_allow_html=True)

    # Nomi giorni localizzati (cal_days_str = "Lun,Mar,...,Dom" nella lingua corrente)
    _day_abbrs = [s.strip() for s in _gt("cal_days_str").split(",")]  # Mon=0 … Sun=6

    cols = st.columns(7)
    for col, day in zip(cols, days):
        with col:
            d       = day["date"]
            rl      = day["risk_level"]
            label   = day["label"]
            conf    = day["confidence"]
            proba   = day["proba"]
            color   = day["color_dark"] if _dark else day["color"]
            txt_col = "#ffffff" if rl > 0 else "#1a3a1a"

            ts       = pd.Timestamp(d)
            day_name = _day_abbrs[ts.dayofweek] if len(_day_abbrs) == 7 else ts.strftime("%a")
            day_num  = ts.strftime("%d/%m")

            bar_low  = round(proba[0] * 100)
            bar_med  = round(proba[1] * 100)
            bar_high = round(proba[2] * 100)

            st.markdown(
                f"""<div style='
                    background:{color};
                    border-radius:10px;
                    padding:10px 6px;
                    text-align:center;
                    min-height:110px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.18);
                '>
                <div style='font-size:0.7rem;color:{txt_col};opacity:0.85;font-weight:600;'>{day_name}</div>
                <div style='font-size:0.72rem;color:{txt_col};opacity:0.75;'>{day_num}</div>
                <div style='font-size:1.05rem;font-weight:700;color:{txt_col};margin:6px 0 2px;'>{label}</div>
                <div style='font-size:0.65rem;color:{txt_col};opacity:0.8;'>conf: {round(conf*100)}%</div>
                <div style='margin-top:6px;height:4px;border-radius:3px;background:rgba(0,0,0,0.15);overflow:hidden;display:flex;'>
                  <div style='width:{bar_low}%;background:#2ecc71;'></div>
                  <div style='width:{bar_med}%;background:#f39c12;'></div>
                  <div style='width:{bar_high}%;background:#e74c3c;'></div>
                </div>
                <div style='font-size:0.55rem;color:{txt_col};opacity:0.6;margin-top:2px;'>B·M·A</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    # ── Legenda ──────────────────────────────────────────────────────────
    leg_c1, leg_c2, leg_c3 = st.columns(3)
    def _leg(col, color, label, desc):
        col.markdown(
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background:{color};border-radius:3px;margin-right:4px;vertical-align:middle;'></span>"
            f"<span style='font-size:0.78rem;'><b>{label}</b> — {desc}</span>",
            unsafe_allow_html=True
        )
    _leg(leg_c1, "#2ecc71", "BASSO",  "attività nella norma")
    _leg(leg_c2, "#f39c12", "MEDIO",  "incremento moderato")
    _leg(leg_c3, "#e74c3c", "ALTO",   "attività elevata")

    # ── Narrazione AI ────────────────────────────────────────────────────
    if ai_text:
        st.markdown("---")
        st.markdown(
            f"<div style='background:{_card_bg};border-radius:10px;padding:14px 18px;"
            f"border-left:4px solid #4a9eff;margin:8px 0;'>"
            f"<p style='font-size:0.78rem;color:{_muted};margin:0 0 6px;font-weight:600;'>🤖 Analisi AI del forecast</p>"
            f"<p style='font-size:0.9rem;margin:0;line-height:1.55;'>{ai_text}</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    # ── Feature importance ───────────────────────────────────────────────
    if top_feats:
        with st.expander("🔍 Feature importanti (cosa guida il modello)", expanded=False):
            _feat_name_map = {
                "n_7d": "N. eventi 7 giorni", "n_3d": "N. eventi 3 giorni",
                "n_14d": "N. eventi 14 giorni", "n_1d": "N. eventi ieri",
                "maxmag_7d": "Magnit. max 7gg", "maxmag_3d": "Magnit. max 3gg",
                "energy_7d": "Energia sismica 7gg", "energy_3d": "Energia sismica 3gg",
                "avgmag_7d": "Magnit. media 7gg", "avgmag_3d": "Magnit. media 3gg",
                "log_energy": "Energia log totale", "log_n_events": "N. eventi (log)",
                "days_since_sig": "Giorni dall'ultimo M≥3", "avg_depth": "Profondità media",
                "doy_sin": "Stagionalità (sin)", "dow_sin": "Giorno settimana (sin)",
            }
            max_imp = max(v for _, v in top_feats) if top_feats else 1
            for fname, fval in top_feats:
                label_f = _feat_name_map.get(fname, fname.replace("_", " "))
                pct     = round(fval / max_imp * 100)
                bar_col = "#4a9eff" if not _dark else "#6ab4ff"
                st.markdown(
                    f"<div style='margin:3px 0;'>"
                    f"<span style='font-size:0.78rem;'>{label_f}</span>"
                    f"<div style='height:6px;border-radius:3px;background:{bar_col};width:{pct}%;margin-top:2px;'></div>"
                    f"<span style='font-size:0.68rem;color:{_muted};'>{round(fval*100,1)}%</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # ── Disclaimer ───────────────────────────────────────────────────────
    st.caption(_gt("ml_disclaimer"))

    # ── Toggle AI narrative ──────────────────────────────────────────────
    with st.expander("⚙️ Impostazioni previsione ML", expanded=False):
        new_ai = st.toggle(
            "Genera narrazione AI del forecast",
            value=st.session_state.get("ml_ai_narrative", True),
            key=f"ml_ai_toggle_{area_key}",
            help="Usa AI (g4f/OpenAI) per spiegare il forecast in linguaggio naturale. "
                 "Può rallentare il caricamento."
        )
        st.session_state["ml_ai_narrative"] = new_ai


# ═══════════════════════════════════════════════════════════════════════════
# PAGINA PREVISIONI
# ═══════════════════════════════════════════════════════════════════════════

def show_predictions_page(earthquake_data, get_text):
    st.header(get_text("predictions_header"))

    st.info(get_text("methodology_note"))

    if earthquake_data is None or earthquake_data.empty:
        st.warning(get_text("no_data"))
        return

    # Dataset esteso 30 giorni per il modello ML (cache 1 ora, separata dal refresh normale)
    _df_ml = fetch_earthquake_data_for_ml(days=30)
    if _df_ml.empty:
        _df_ml = earthquake_data  # fallback al dataset normale se fetch fallisce

    areas = ["Italy", "Vesuvio", "Campi Flegrei", "Ischia"]
    area_data_map = {
        "Italy": earthquake_data,
        "Vesuvio": filter_area_earthquakes(earthquake_data, "vesuvio"),
        "Campi Flegrei": filter_area_earthquakes(earthquake_data, "campi_flegrei"),
        "Ischia": filter_area_earthquakes(earthquake_data, "ischia"),
    }
    # Mappa ML: Italia usa 30gg nazionale; vulcani usano fetch dedicato 90gg a soglia M0
    _df_ml_vesuvio = fetch_earthquake_data_for_ml_area("vesuvio", days=90)
    _df_ml_cf      = fetch_earthquake_data_for_ml_area("campi_flegrei", days=90)
    _df_ml_ischia  = fetch_earthquake_data_for_ml_area("ischia", days=90)
    area_data_map_ml = {
        "Italy":         _df_ml,
        "Vesuvio":       _df_ml_vesuvio if not _df_ml_vesuvio.empty else filter_area_earthquakes(_df_ml, "vesuvio"),
        "Campi Flegrei": _df_ml_cf      if not _df_ml_cf.empty      else filter_area_earthquakes(_df_ml, "campi_flegrei"),
        "Ischia":        _df_ml_ischia  if not _df_ml_ischia.empty   else filter_area_earthquakes(_df_ml, "ischia"),
    }

    area_tabs = st.tabs(["Italia", "🌋 Vesuvio", "🔥 Campi Flegrei", "🏝️ Ischia"])

    for tab, area in zip(area_tabs, areas):
        with tab:
            area_df    = area_data_map[area]
            area_df_ml = area_data_map_ml.get(area, area_df)
            area_key   = area.replace(" ", "_").lower()

            # Se no dati 7gg mostra info ma prosegui con la sezione ML (dati 90gg)
            if area_df is None or area_df.empty:
                st.info(get_text("no_events_area"))
                _show_ml_forecast_calendar(area_df_ml, area, area_key)
                continue

            stats = calculate_earthquake_statistics(area_df)
            risk_level, risk_metrics = calculate_risk_level(stats, area)

            # Stima probabilistica scientifica (Poisson + G-R + Omori)
            forecast = get_seismic_forecast(area_df, area)
            if forecast and forecast.get("prob_table"):
                pt = forecast["prob_table"]
                gr = forecast.get("gutenberg_richter", {})
                st.subheader("📊 Stima Probabilistica Sismicità")
                st.markdown(
                    "<p style='font-size:0.82rem;color:#888;margin:-6px 0 10px;'>"
                    "P(almeno 1 evento) calcolata con <b>processo di Poisson</b> + "
                    "<b>Gutenberg-Richter</b> sui dati INGV/USGS reali. "
                    "Non è previsione deterministica — nessun sistema al mondo lo è.</p>",
                    unsafe_allow_html=True,
                )
                fc_cols = st.columns(3)
                for col, (label, N) in zip(fc_cols, [("24 ore", 1), ("7 giorni", 7), ("30 giorni", 30)]):
                    with col:
                        p_m2 = pt.get(2.0, {}).get(N, 0)
                        p_m3 = pt.get(3.0, {}).get(N, 0)
                        st.metric(
                            f"P(≥M2) in {label}",
                            f"{p_m2}%",
                            f"P(≥M3) = {p_m3}%",
                        )
                b_val = gr.get("b", "—")
                n_ev  = forecast.get("n_events_used", "—")
                lam   = forecast.get("rate_per_day", 0)
                method= forecast.get("method", "Poisson + G-R")
                st.caption(
                    f"Metodo: {method} · "
                    f"Tasso: {lam:.2f} eventi/giorno · "
                    f"b-value: {b_val} · "
                    f"Campione: {n_ev} eventi ≥M1.5"
                )

            col1, col2 = st.columns(2)
            with col1:
                _plot_magnitude_distribution(area_df, f"{_gt('mag_dist_prefix')} — {area}", plot_key=f"pred_{area_key}")
            with col2:
                _plot_depth_distribution(area_df, f"{_gt('depth_dist_prefix')} — {area}", plot_key=f"pred_{area_key}")

            _plot_seismic_energy_timeseries(area_df, area, plot_key=f"pred_{area_key}")
            show_magnitude_time_chart(area_df, area, get_text, show_risk=False)

            _show_ml_forecast_calendar(area_df_ml, area, area_key)
            _show_advice(risk_level)


def _show_advice(risk_level):
    st.subheader(_gt("recommendations_title"))
    advice = {
        "basso": {
            f"🟢 {_gt('situation')}": _gt("advice_basso_sit"),
            f"🏠 {_gt('home')}": _gt("advice_basso_home"),
            f"📱 {_gt('communications')}": _gt("advice_basso_comm"),
        },
        "moderato": {
            f"🟡 {_gt('situation')}": _gt("advice_mod_sit"),
            f"🏠 {_gt('home')}": _gt("advice_mod_home"),
            f"📱 {_gt('communications')}": _gt("advice_mod_comm"),
        },
        "elevato": {
            f"🟠 {_gt('situation')}": _gt("advice_elev_sit"),
            f"🏠 {_gt('home')}": _gt("advice_elev_home"),
            f"📱 {_gt('communications')}": _gt("advice_elev_comm"),
        },
        "molto elevato": {
            f"🔴 {_gt('situation')}": _gt("advice_molt_sit"),
            f"🏠 {_gt('action')}": _gt("advice_molt_action"),
            f"📞 {_gt('emergency')}": _gt("advice_molt_emerg"),
        },
    }
    advice_data = advice.get(risk_level, advice["basso"])
    cols = st.columns(len(advice_data))
    for col, (title, text) in zip(cols, advice_data.items()):
        with col:
            st.markdown(f"**{title}**")
            st.markdown(text)
    st.markdown("---")
    st.markdown(
        f"**{_gt('emergency_contacts_label')}**: "
        "📞 **112** · 📞 **800 232525** (Prot. Civile Campania) · "
        "🌐 [INGV](https://www.ingv.it) · "
        "🌐 [Protezione Civile](https://www.protezionecivile.gov.it)"
    )


# ═══════════════════════════════════════════════════════════════════════════
# CALCOLO LIVELLO DI RISCHIO — basato su dati reali INGV/USGS
# ═══════════════════════════════════════════════════════════════════════════

def calculate_risk_level(stats, area):
    risk_metrics = {
        "event_frequency": 0.0, "magnitude_risk": 0.0, "depth_risk": 0.0,
        "spatial_density": 0.0, "temporal_trend": 0.0,
        "acceleration": 0.0, "clustering": 0.0,
    }

    if stats["count"] == 0:
        return "basso", risk_metrics

    recent_count = sum(v for k, v in stats["daily_counts"].items()
                       if pd.to_datetime(k) >= pd.Timestamp.now() - pd.Timedelta(days=3))
    older_count = sum(v for k, v in stats["daily_counts"].items()
                      if pd.to_datetime(k) < pd.Timestamp.now() - pd.Timedelta(days=3))
    acceleration = recent_count / (older_count + 1)
    risk_metrics["acceleration"] = min(acceleration / 2, 1.0)

    mag_thresh = 2.0 if area == "Campi Flegrei" else 2.5
    risk_metrics["magnitude_risk"] = max(0.0, min((stats["max_magnitude"] - mag_thresh) / 3.0, 1.0))

    depth_w = 1.5 if area == "Campi Flegrei" else 1.0
    risk_metrics["depth_risk"] = min(max(0.0, (20 - stats["avg_depth"]) / 20 * depth_w), 1.0)

    freq_thresh = 30 if area == "Campi Flegrei" else 20
    risk_metrics["event_frequency"] = min(stats["count"] / freq_thresh, 1.0)

    if len(stats["daily_counts"]) > 1:
        values = list(stats["daily_counts"].values())
        risk_metrics["clustering"] = min(np.std(values) / (np.mean(values) + 1), 1.0)

    weights = {
        "Campi Flegrei": {"event_frequency": 0.25, "magnitude_risk": 0.20,
                          "depth_risk": 0.25, "acceleration": 0.20, "clustering": 0.10},
        "Vesuvio": {"event_frequency": 0.20, "magnitude_risk": 0.30,
                    "depth_risk": 0.20, "acceleration": 0.20, "clustering": 0.10},
        "default": {"event_frequency": 0.20, "magnitude_risk": 0.25,
                    "depth_risk": 0.20, "acceleration": 0.25, "clustering": 0.10},
    }
    w = weights.get(area, weights["default"])
    score = sum(risk_metrics[k] * v for k, v in w.items())

    if score < 0.3:
        return "basso", risk_metrics
    elif score < 0.5:
        return "moderato", risk_metrics
    elif score < 0.7:
        return "elevato", risk_metrics
    else:
        return "molto elevato", risk_metrics
