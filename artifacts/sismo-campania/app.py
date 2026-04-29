import os
import logging
import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
import locale

# Sopprimi log DEBUG da watchdog, urllib3, PIL, matplotlib
for _noisy in ("watchdog", "urllib3", "PIL", "matplotlib", "asyncio"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

import data_service
import visualization
import emergenza
import weather
import forum
import utils
import ai_analysis
import ai_chat

# Impostiamo la localizzazione italiana per i nomi dei giorni
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')  # Linux/macOS
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Italian_Italy')  # Windows
    except:
        pass  # Se fallisce, useremo una mappatura manuale

# Mappatura manuale inglese-italiano per i giorni della settimana
giorni_settimana = {
    'Monday': 'Lunedì',
    'Tuesday': 'Martedì',
    'Wednesday': 'Mercoledì',
    'Thursday': 'Giovedì',
    'Friday': 'Venerdì',
    'Saturday': 'Sabato',
    'Sunday': 'Domenica'
}

# Configure page settings
st.set_page_config(
    page_title="Monitoraggio Sismico - Campania",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'About': '### Monitoraggio Sismico - Campania\nSviluppato da Fabio SCELZO'
    }
)

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=600_000, key="auto_refresh_main")  # 10 minuti

import orario
ora = orario.get_orario()
from translations_lib import get_text, TRANSLATIONS

# Initialize session state variables if they don't exist
if 'language' not in st.session_state:
    st.session_state.language = 'it'
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'last_data_fetch' not in st.session_state:
    st.session_state.last_data_fetch = None
if 'earthquake_data' not in st.session_state:
    st.session_state.earthquake_data = None
if 'notification_enabled' not in st.session_state:
    st.session_state.notification_enabled = False
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = {}
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'last_weather_fetch' not in st.session_state:
    st.session_state.last_weather_fetch = None

# === CONTATORE VISITE (una sola volta per sessione) ===
from security import read_visit_counter, increment_visit_counter
if 'visit_counted' not in st.session_state:
    st.session_state.visit_counted = False
if not st.session_state.visit_counted:
    increment_visit_counter()
    st.session_state.visit_counted = True
_visit_count = read_visit_counter()

# Carica stile CSS personalizzato (light sempre; dark sovrapposto se attivo)
_base_dir = os.path.dirname(__file__)
_css_dirs = [
    os.path.join(_base_dir, 'SeismicSafetyItalia', 'streamlit'),
    os.path.join(_base_dir, 'streamlit'),
]
for _css_dir in _css_dirs:
    _style_path = os.path.join(_css_dir, 'style.css')
    if os.path.exists(_style_path):
        try:
            with open(_style_path) as _f:
                st.markdown(f'<style>{_f.read()}</style>', unsafe_allow_html=True)
        except Exception:
            pass
        break
if st.session_state.dark_mode:
    for _css_dir in _css_dirs:
        _dark_path = os.path.join(_css_dir, 'dark.css')
        if os.path.exists(_dark_path):
            try:
                with open(_dark_path) as _f:
                    st.markdown(f'<style>{_f.read()}</style>', unsafe_allow_html=True)
            except Exception:
                pass
            break


# Translations are in translations_lib.py

# Funzione per tradurre i nomi dei giorni in italiano
def traduci_giorno(giorno_en):
    return giorni_settimana.get(giorno_en, giorno_en)

# Weather e meteo ora gestiti da weather.py (Open-Meteo, no API key, GPS, 7gg forecast)

# Sidebar for navigation and settings
with st.sidebar:
    st.markdown(
        "<h2 style='margin-bottom:2px;'>🌋 Monitoraggio Sismico</h2>"
        "<p style='font-size:13px;color:#888;margin-top:0;'>Real Time — Campania</p>",
        unsafe_allow_html=True
    )

    # Orologio compatto
    st.markdown(
        f"<div style='background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 12px;margin-bottom:8px;"
        f"font-size:13px;color:#f1faee;'>"
        f"🕐 <b>{get_text('italia_time_label')}:</b> {ora['italia']} <span style='color:rgba(255,255,255,0.6)'>| UTC: {ora['utc']}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    # ── Lingua ─────────────────────────────────────────────────────────────
    lang_options = {
        'it': '🇮🇹 Italiano',
        'en': '🇬🇧 English',
        'fr': '🇫🇷 Français',
        'es': '🇪🇸 Español',
        'de': '🇩🇪 Deutsch',
        'pt': '🇵🇹 Português',
        'zh': '🇨🇳 中文',
        'ja': '🇯🇵 日本語',
        'ru': '🇷🇺 Русский',
        'ar': '🇸🇦 العربية',
    }
    current_lang = st.session_state.language if st.session_state.language in lang_options else 'it'
    selected_lang = st.selectbox(
        f"🌐 {get_text('language')}",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(current_lang),
        label_visibility="visible",
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

    # ── Dark / Light mode toggle ────────────────────────────────────────────
    dark_icon = "🌙" if not st.session_state.dark_mode else "☀️"
    dark_label = f"{dark_icon} {get_text('dark_mode_label')}"
    new_dark = st.toggle(dark_label, value=st.session_state.dark_mode, key="dark_mode_toggle")
    if new_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark
        st.rerun()

    st.markdown("---")

    # ── Alert livelli allerta ───────────────────────────────────────────────
    st.markdown(f"**🚨 {get_text('alert_levels')}**")
    st.markdown(
        f"""<div style="display:flex;flex-direction:column;gap:5px;margin-bottom:4px;">
<div style="background:rgba(39,174,96,0.25);border:1px solid #27ae60;border-radius:7px;padding:6px 10px;">
  <span style="font-size:12px;font-weight:700;color:#d4f7e0;">🟢 Vesuvio</span>
  <span style="font-size:11px;color:#d4f7e0;float:right;">{get_text('alert_verde')}</span>
</div>
<div style="background:rgba(243,156,18,0.25);border:1px solid #f39c12;border-radius:7px;padding:6px 10px;">
  <span style="font-size:12px;font-weight:700;color:#fff3cd;">🟡 Campi Flegrei</span>
  <span style="font-size:11px;color:#fff3cd;float:right;">{get_text('alert_giallo')}</span>
</div>
<div style="background:rgba(39,174,96,0.25);border:1px solid #27ae60;border-radius:7px;padding:6px 10px;">
  <span style="font-size:12px;font-weight:700;color:#d4f7e0;">🟢 Ischia</span>
  <span style="font-size:11px;color:#d4f7e0;float:right;">{get_text('alert_verde')}</span>
</div></div>
<p style="font-size:10px;color:rgba(255,255,255,0.6);margin:0;">{get_text('fonte_ingv_ov')}</p>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation menu
    st.markdown(f"**📋 {get_text('menu')}**")
    page = st.radio(
        "Navigation",
        ["monitoring", "predictions", "weather", "ai_assistant", "emergency", "community", "about"],
        format_func=lambda x: get_text(x),
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Refresh data button
    if st.button(get_text('refresh'), use_container_width=True, type="primary"):
        with st.spinner(get_text('updating')):
            st.session_state.earthquake_data = data_service.fetch_earthquake_data()
            st.session_state.last_data_fetch = datetime.now()
            st.rerun()

    # Notification toggle
    st.checkbox(
        get_text('enable_notifications'),
        value=st.session_state.notification_enabled,
        key="notification_toggle",
        on_change=utils.toggle_notifications
    )

    st.caption(f"👥 Visite totali: **{_visit_count:,}**")

    # Last update timestamp + data quality badge
    if st.session_state.last_data_fetch:
        age_s = (datetime.now() - st.session_state.last_data_fetch).total_seconds()
        if age_s < 300:
            _dq_icon, _dq_color, _dq_label = "✅", "#27ae60", "live"
        elif age_s < 1200:
            _dq_icon, _dq_color, _dq_label = "⚠️", "#e67e22", "cache"
        else:
            _dq_icon, _dq_color, _dq_label = "❌", "#c0392b", "non aggiornato"
        _fetch_str = st.session_state.last_data_fetch.strftime('%d/%m %H:%M:%S')
        st.markdown(
            f"<p style='font-size:0.78rem;color:#888;margin:2px 0;'>"
            f"🔄 {get_text('last_update')}: {_fetch_str} "
            f"<span style='color:{_dq_color};font-weight:700;'>{_dq_icon} {_dq_label}</span></p>",
            unsafe_allow_html=True,
        )

    st.caption(get_text('data_source'))

    # ── Alert eventi significativi recenti (≥M3 ultime 24h) ────────────────
    _eq = st.session_state.get("earthquake_data")
    if _eq is not None and not _eq.empty:
        try:
            _eq2 = _eq.copy()
            _eq2["datetime"] = pd.to_datetime(_eq2["datetime"], errors="coerce")
            _cut24 = datetime.now() - timedelta(hours=24)
            def _zona(row):
                lat, lon = row.get("latitude", 0), row.get("longitude", 0)
                if 39.9 <= lat <= 41.5 and 13.5 <= lon <= 16.0:
                    return "campania"
                if 35.5 <= lat <= 47.1 and 6.6 <= lon <= 18.55:
                    return "italia"
                return "mondo"

            _sig = _eq2[(_eq2["datetime"] >= _cut24) & (_eq2["magnitude"] >= 3.0)]
            _all24 = _eq2[_eq2["datetime"] >= _cut24].sort_values("datetime", ascending=False)
            if not _sig.empty or not _all24.empty:
                _top_forte = _sig.sort_values("magnitude", ascending=False).iloc[0] if not _sig.empty else None
                _top_rec   = _all24.iloc[0] if not _all24.empty else None
                _stesso = (
                    _top_forte is not None
                    and _top_rec is not None
                    and _top_forte.get("location", "") == _top_rec.get("location", "")
                    and _top_forte["datetime"] == _top_rec["datetime"]
                )

                def _banner_html(row, etichetta, icona):
                    _Mm   = row["magnitude"]
                    _loc  = str(row.get("location", "n/d"))[:30]
                    _ts   = row["datetime"].strftime("%d/%m %H:%M") if pd.notnull(row["datetime"]) else ""
                    _z    = _zona(row)
                    if _z == "campania":
                        _flag   = "<img src='https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f30b.png' width='18' style='vertical-align:middle'>"
                        _col    = "#c0392b" if _Mm >= 4.0 else "#e67e22" if _Mm >= 3.5 else "#d35400"
                        _border = "2px solid #fff"
                        _opacity = "1"
                    elif _z == "italia":
                        _flag   = "<img src='https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f1ee-1f1f9.png' width='18' style='vertical-align:middle'>"
                        _col    = "#1a6e3a" if _Mm >= 4.0 else "#27ae60" if _Mm >= 3.0 else "#2ecc71"
                        _border = "1px solid rgba(255,255,255,0.4)"
                        _opacity = "0.92"
                    else:
                        _flag   = "<img src='https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/1f30d.png' width='18' style='vertical-align:middle'>"
                        _col    = "#5d6d7e"
                        _border = "1px solid rgba(255,255,255,0.2)"
                        _opacity = "0.75"
                    return (
                        f"<div style='background:{_col};border-radius:8px;padding:9px 11px;"
                        f"margin:6px 0 2px 0;border:{_border};opacity:{_opacity};'>"
                        f"<div style='color:#fff;font-size:0.84rem;font-weight:800;'>"
                        f"{icona} {_flag} {etichetta} M{_Mm:.1f} — ULTIME 24H</div>"
                        f"<div style='color:#ffe0e0;font-size:0.75rem;margin-top:3px;'>{_loc}</div>"
                        f"<div style='color:#ffbbbb;font-size:0.72rem;'>{_ts}</div>"
                        f"</div>"
                    )

                if _stesso and _top_forte is not None:
                    st.markdown(
                        _banner_html(_top_forte, "EVENTO PIÙ FORTE / PIÙ RECENTE", "🔴"),
                        unsafe_allow_html=True,
                    )
                else:
                    if _top_forte is not None:
                        st.markdown(
                            _banner_html(_top_forte, "EVENTO PIÙ FORTE (24H)", "🔴"),
                            unsafe_allow_html=True,
                        )
                    if _top_rec is not None:
                        st.markdown(
                            _banner_html(_top_rec, "ULTIMO EVENTO", "🟠"),
                            unsafe_allow_html=True,
                        )
        except Exception:
            pass

    # ── Link rapidi ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"**🔗 {get_text('quick_links')}**")
    st.markdown(
        "[🌍 Terremoti INGV live](https://terremoti.ingv.it/)  \n"
        "[🛡️ Protezione Civile](https://www.protezionecivile.gov.it/)"
    )

    # ── App correlata: SOS Italia ──────────────────────────────────────────
    st.markdown(
        "<div style='background:rgba(230,57,70,0.18);border:1px solid #e63946;"
        "border-radius:9px;padding:10px 12px;margin-top:6px;'>"
        "<p style='color:#fff;font-size:12px;font-weight:700;margin:0 0 4px 0;'>"
        "🆘 App correlata</p>"
        "<p style='color:#f1faee;font-size:11px;margin:0 0 7px 0;'>"
        "Emergenze in Italia — numeri utili, piani evacuazione, allerte meteo</p>"
        "<a href='https://sos-italia.streamlit.app' target='_blank' "
        "style='display:block;text-align:center;background:#e63946;color:#fff;"
        "padding:7px 10px;border-radius:7px;font-size:12px;font-weight:700;"
        "text-decoration:none;'>🔗 Apri SOS Italia →</a>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Sostieni il progetto ───────────────────────────────────────────────
    st.markdown("---")
    _support = get_text('support_project')
    _coffee = get_text('buy_coffee')
    st.markdown(
        f"""<div style="background:rgba(255,255,255,0.1);padding:12px 14px;
border-radius:10px;border:1px solid #e63946;margin-top:4px;">
<p style="color:#f1faee;font-size:11px;margin:0 0 8px 0;text-align:center;letter-spacing:.05em;">
☕ {_support}</p>
<a href="https://www.paypal.com/donate/?business=meteotorre@gmail.com" target="_blank"
class="donate-btn"
style="display:block;text-align:center;background:linear-gradient(135deg,#f7971e,#ffd200);
color:#1a1a1a !important;padding:9px 14px;text-decoration:none;border-radius:8px;font-size:14px;
font-weight:800;letter-spacing:.03em;box-shadow:0 3px 10px rgba(255,210,0,.4);">
☕ {_coffee}
</a></div>""",
        unsafe_allow_html=True,
    )

# Main content area
st.title("🌋 " + get_text('title'))
st.subheader(get_text('subtitle'))

# Check if we need to fetch data
if st.session_state.earthquake_data is None or (
    st.session_state.last_data_fetch and 
    datetime.now() - st.session_state.last_data_fetch > timedelta(minutes=15)
):
    with st.spinner(get_text('updating')):
        from concurrent.futures import ThreadPoolExecutor as _TPE
        import ingv_monitor as _im
        # ── Prefetch parallelo: sismicità + INGV OV + GPS + AQ ──────────────
        with _TPE(max_workers=8) as _ex:
            _feq   = _ex.submit(data_service.fetch_earthquake_data)
            _fbv   = _ex.submit(_im.fetch_bulletin_values_live)
            _fal   = _ex.submit(_im.fetch_ingv_alert_level)
            _fgps  = _ex.submit(_im.fetch_gps_rite)
            _fgpsv = _ex.submit(_im.fetch_gps_vesuvio)
            _faq   = _ex.submit(_im.fetch_air_quality_campania)
            _faqv  = _ex.submit(_im.fetch_air_quality_vesuvio)
            _fst   = _ex.submit(_im.fetch_summit_temperature, 40.821, 14.126, 1281, "Vesuvio")
            st.session_state.earthquake_data = _feq.result()
            for _fut in (_fbv, _fal, _fgps, _fgpsv, _faq, _faqv, _fst):
                try: _fut.result()
                except Exception: pass
        st.session_state.last_data_fetch = datetime.now()
        st.rerun()

def _ai_card(icon, title, headline, body, color, extra=""):
    """Card grande e leggibile per un risultato AI."""
    st.markdown(
        f"""<div style="border:2px solid {color};border-radius:12px;
padding:18px 20px;margin-bottom:16px;background:#fff;">
  <div style="font-size:13px;font-weight:700;color:#666;
letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px;">
    {icon} {title}
  </div>
  <div style="font-size:20px;font-weight:800;color:{color};
margin-bottom:8px;line-height:1.3;">{headline}</div>
  <div style="font-size:14px;color:#333;line-height:1.5;">{body}</div>
  {f'<div style="font-size:12px;color:#888;margin-top:8px;">{extra}</div>' if extra else ''}
</div>""",
        unsafe_allow_html=True,
    )


def _render_ai_panel(anomaly, pattern, bvalue, gps_corr):
    """Rende il pannello AI analysis per un'area — card grandi e leggibili."""

    # 1. Anomaly Detection
    if anomaly and anomaly.get("status") != "insufficient_data":
        is_anom = anomaly.get("anomaly", False)
        color   = "#dc3545" if is_anom else "#198754"
        icon    = "⚠️" if is_anom else "✅"
        hl      = "ANOMALIA RILEVATA" if is_anom else "Attività nella norma"
        body    = anomaly.get("explanation", "")
        extra   = (f"Ultimi 3gg: {anomaly.get('recent_count','?')} eventi · "
                   f"Media storica: {anomaly.get('baseline_daily_avg', 0):.1f}/giorno")
        _ai_card(icon, "Anomaly Detection (Isolation Forest)", hl, body, color, extra)
    elif anomaly:
        st.info(f"🔍 Anomaly Detection: {anomaly.get('explanation','Dati insufficienti')}")

    # 2. Pattern Classifier
    if pattern and pattern.get("pattern") not in ("sconosciuto", None):
        pat = pattern.get("pattern", "")
        colors_map = {"sciame": "#0d6efd", "sequenza": "#fd7e14",
                      "isolato": "#6c757d", "silenzio": "#198754"}
        icons_map  = {"sciame": "🔵", "sequenza": "🟠",
                      "isolato": "⚪", "silenzio": "🟢"}
        color = colors_map.get(pat, "#6c757d")
        icon  = icons_map.get(pat, "❓")
        hl    = pattern.get("label", pat.upper())
        body  = pattern.get("description", "")
        extra = (f"Confidenza: {pattern.get('confidence',0)*100:.0f}% · "
                 f"{pattern.get('n_events',0)} eventi analizzati · "
                 f"{pattern.get('n_clusters',0)} cluster")
        _ai_card(icon, "Classificazione Pattern (DBSCAN)", hl, body, color, extra)

    # 3. Gutenberg-Richter b-value
    if bvalue and bvalue.get("status") == "ok":
        b     = bvalue.get("b_value", 0)
        color = "#dc3545" if b < 0.7 else "#fd7e14" if b < 0.9 else "#198754"
        hl    = f"b = {b:.3f}"
        body  = bvalue.get("interpretation", "")
        extra = (f"N eventi sopra Mc: {bvalue.get('n_events','?')} · "
                 f"Mc = {bvalue.get('mc','?')} · R² = {bvalue.get('r_squared','?')}")
        _ai_card("📊", "Gutenberg-Richter b-value", hl, body, color, extra)
    elif bvalue:
        st.info(f"📊 b-value: {bvalue.get('interpretation','Dati insufficienti')}")

    # 4. GPS + Sismicità (solo CF)
    if gps_corr and gps_corr.get("level") not in ("no_gps", "no_seismic", None):
        alert = gps_corr.get("alert", False)
        color = "#dc3545" if alert else "#198754"
        icon  = "⚠️" if alert else "✅"
        hl    = "SEGNALE COMPOSITO ELEVATO" if alert else "Parametri nella norma"
        body  = gps_corr.get("message", "")
        _ai_card(icon, "Correlazione GPS + Sismicità", hl, body, color)


# Display the selected page content
if page == "monitoring":
    visualization.show_monitoring_page(st.session_state.earthquake_data, get_text)

elif page == "weather":
    st.header(f"🌤️ {get_text('weather')}")
    weather.show_meteo()

elif page == "predictions":
    visualization.show_predictions_page(st.session_state.earthquake_data, get_text)

elif page == "ai_assistant":
    st.header("🤖 Assistente AI Sismico")
    st.markdown(
        "Analisi avanzata basata su modelli AI/ML sui dati live INGV. "
        "Usa la chat per domande in linguaggio naturale, oppure consulta le analisi automatiche."
    )

    eq_data = st.session_state.earthquake_data
    from data_service import filter_area_earthquakes
    import ingv_monitor
    cf_df  = filter_area_earthquakes(eq_data, "campi_flegrei") if eq_data is not None else None
    ves_df = filter_area_earthquakes(eq_data, "vesuvio")       if eq_data is not None else None
    isc_df = filter_area_earthquakes(eq_data, "ischia")        if eq_data is not None else None

    bulletin_live = ingv_monitor.fetch_bulletin_values_live()
    bulletin_cf   = bulletin_live.get("campi_flegrei", ingv_monitor.get_ingv_bulletin_values().get("campi_flegrei", {}))
    bulletin_ves  = bulletin_live.get("vesuvio",       ingv_monitor.get_ingv_bulletin_values().get("vesuvio", {}))
    alert         = ingv_monitor.fetch_ingv_alert_level() or {}
    gps           = ingv_monitor.fetch_gps_rite()

    # ── Carica dati AI per tutte le aree ─────────────────────────────────────
    with st.spinner("⏳ Modelli AI in esecuzione sui dati INGV..."):
        anomaly_cf  = ai_analysis.detect_anomalies(cf_df,  "campi_flegrei") if cf_df  is not None and not cf_df.empty  else {}
        pattern_cf  = ai_analysis.classify_seismic_pattern(cf_df,  "campi_flegrei") if cf_df  is not None and not cf_df.empty  else {}
        bvalue_cf   = ai_analysis.compute_gutenberg_richter(cf_df,  "campi_flegrei") if cf_df  is not None and not cf_df.empty  else {}
        gps_corr_cf = ai_analysis.compute_gps_seismicity_correlation(cf_df, gps)
        anomaly_ves = ai_analysis.detect_anomalies(ves_df, "vesuvio")       if ves_df is not None and not ves_df.empty else {}
        pattern_ves = ai_analysis.classify_seismic_pattern(ves_df, "vesuvio")       if ves_df is not None and not ves_df.empty else {}
        bvalue_ves  = ai_analysis.compute_gutenberg_richter(ves_df, "vesuvio")       if ves_df is not None and not ves_df.empty else {}
        anomaly_isc = ai_analysis.detect_anomalies(isc_df, "ischia")        if isc_df is not None and not isc_df.empty else {}
        pattern_isc = ai_analysis.classify_seismic_pattern(isc_df, "ischia")        if isc_df is not None and not isc_df.empty else {}
        bvalue_isc  = ai_analysis.compute_gutenberg_richter(isc_df, "ischia")        if isc_df is not None and not isc_df.empty else {}

    # ── Tab CF / Vesuvio / Ischia / Chat AI ──────────────────────────────────
    tab_cf, tab_ves, tab_isc, tab_chat = st.tabs(
        ["🔴 Campi Flegrei", "🌋 Vesuvio", "🏝️ Ischia", "🤖 Chat AI"]
    )

    with tab_cf:
        st.markdown("### Analisi AI — Campi Flegrei")
        if cf_df is None or cf_df.empty:
            st.warning("Nessun dato sismico disponibile per i Campi Flegrei.")
        else:
            st.caption(f"Basata su {len(cf_df)} eventi INGV/USGS nell'ultimo periodo")
            _render_ai_panel(anomaly_cf, pattern_cf, bvalue_cf, gps_corr_cf)

    with tab_ves:
        st.markdown("### Analisi AI — Vesuvio")
        if ves_df is None or ves_df.empty:
            st.warning("Nessun dato sismico disponibile per il Vesuvio.")
        else:
            st.caption(f"Basata su {len(ves_df)} eventi INGV/USGS nell'ultimo periodo")
            _render_ai_panel(anomaly_ves, pattern_ves, bvalue_ves, None)

    with tab_isc:
        st.markdown("### Analisi AI — Ischia")
        st.info(
            "🏝️ **Nota Ischia**: La sismicità è prevalentemente tettonica superficiale (<5 km). "
            "L'anomaly detection e il b-value sono particolarmente utili per identificare "
            "sequenze sismiche precursori di eventi come quello del 2022 (M 5.7)."
        )
        if isc_df is None or isc_df.empty:
            st.success("✅ Nessun evento sismico recente nell'area di Ischia — attività nella norma.")
        else:
            st.caption(f"Basata su {len(isc_df)} eventi INGV/USGS nell'ultimo periodo")
            _render_ai_panel(anomaly_isc, pattern_isc, bvalue_isc, None)

    with tab_chat:
        ai_chat.show_ai_chat(
            earthquake_data=eq_data,
            bulletin_cf=bulletin_cf,
            bulletin_ves=bulletin_ves,
            alert_level=alert or {},
            gps_data=gps,
            anomaly_cf=anomaly_cf if cf_df is not None else None,
            pattern_cf=pattern_cf if cf_df is not None else None,
            bvalue_cf=bvalue_cf if cf_df is not None else None,
            lang=st.session_state.get("language", "it"),
        )

elif page == "emergency":
    emergenza.show()
elif page == "community":
    forum.main()
elif page == "about":
    st.header(get_text('about_title'))
    
    st.subheader(get_text('about_app_title'))
    st.markdown(get_text('about_app_desc'))
    
    st.markdown("---")
    
    # Developer section
    st.subheader(get_text('about_developer'))
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # URL raw dell'immagine su GitHub
        img_url = "https://raw.githubusercontent.com/ScelzoF/SeismicSafetyItalia/main/assets/fabio_scelzo.jpg"
        
        # Utilizziamo un riquadro rettangolare (non rotondo) senza bordi arrotondati
        st.markdown("""
        <style>
        .profile-image {
            max-width: 100%;
            border: 1px solid #ddd;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        </style>
        <div style="text-align: center; padding: 10px;">
            <img src="https://raw.githubusercontent.com/ScelzoF/SeismicSafetyItalia/main/assets/fabio_scelzo.jpg" class="profile-image" width="180">
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### Fabio Scelzo
        
        Nato nel 1973, Fabio ha coltivato sin dall'infanzia una profonda passione per l'elettronica e l'informatica, 
        che è rimasta costante attraverso gli anni, evolvendo insieme alle tecnologie.
        
        Esperto di sviluppo software e appassionato di monitoraggio ambientale, ha creato questa piattaforma per 
        fornire uno strumento utile alla comunità, combinando competenze tecniche e interesse per il territorio. 
        Lo sviluppo è stato potenziato dall'utilizzo delle moderne tecnologie di Intelligenza Artificiale, 
        che hanno contribuito a migliorarne le funzionalità e l'interfaccia utente.
        
        Attualmente vive a **Torre Annunziata**, una città ricca di storia e tradizioni nella provincia di Napoli.
        """)
    
    st.markdown("---")
    
    # Sezione su Torre Annunziata
    st.subheader("🏙️ Torre Annunziata: Una Città tra Storia e Mare")
    
    st.markdown("""
    **Torre Annunziata** è una pittoresca città costiera situata ai piedi del Vesuvio, affacciata sul suggestivo Golfo di Napoli. 
    Con una storia che affonda le radici nell'antica Roma, la città conserva ancora i resti dell'antica *Oplontis*, una delle ville suburbane 
    sepolte dall'eruzione del Vesuvio nel 79 d.C. e oggi patrimonio UNESCO insieme a Pompei ed Ercolano.
    
    ### Tradizione e Industria
    
    La città è rinomata per la sua storica tradizione nella produzione della pasta. I pastifici di Torre Annunziata, 
    favoriti dalle pure acque sorgive provenienti dal Sarno e dal particolare microclima, hanno rappresentato per secoli un'eccellenza mondiale. 
    L'arte della pasta trova qui uno dei suoi luoghi d'origine, con tecniche tramandate di generazione in generazione.
    
    ### Mare e Territorio
    
    Con le sue spiagge di sabbia nera vulcanica, Torre Annunziata offre un paesaggio unico dove il blu del mare incontra 
    la maestosità del Vesuvio. Il lungomare, recentemente riqualificato, è diventato un punto di ritrovo per residenti e turisti.
    
    ### Cultura e Sport
    
    Nel panorama sportivo, la città è rappresentata con orgoglio dal **Savoia Calcio**, storica squadra fondata nel 1908, che ha vissuto 
    momenti di gloria nel calcio italiano. I colori bianco e nero della squadra sono un simbolo identitario forte per la comunità locale.
    
    La città vanta inoltre un ricco patrimonio culturale, con manifestazioni folkloristiche che tramandano tradizioni secolari, 
    e una gastronomia che rispecchia la migliore tradizione culinaria campana.
    """)
    
    st.markdown("---")
    
    st.markdown(f"""
    ### {get_text('about_contacts')}
    
    📧 Email: meteotorre@gmail.com
    
    ---
    👥 **Visite totali:** {_visit_count:,} &nbsp;|&nbsp; © {datetime.now().year} Monitoraggio Sismico Campania
    """)

# Check for significant earthquakes and show alert if notifications are enabled
if st.session_state.notification_enabled and st.session_state.earthquake_data is not None:
    significant_eq = data_service.get_significant_earthquakes(st.session_state.earthquake_data)
    if not significant_eq.empty:
        for _, eq in significant_eq.iterrows():
            st.toast(f"⚠️ {get_text('magnitude')}: {eq['magnitude']} - {eq['location']}")

# === AUTO-REFRESH DATI ===
# Forza il refresh dei dati sismici ogni 15 minuti anche senza interazione
import time as _time
if 'last_auto_refresh' not in st.session_state:
    st.session_state.last_auto_refresh = _time.time()

_auto_elapsed = _time.time() - st.session_state.last_auto_refresh
if _auto_elapsed > 900:  # 15 minuti
    st.session_state.last_auto_refresh = _time.time()
    st.session_state.earthquake_data = None
    st.rerun()

