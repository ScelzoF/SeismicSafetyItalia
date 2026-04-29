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

@st.dialog("💳 Dati per donazione PostePay")
def _show_postepay_dialog():
    st.markdown("Invia direttamente tramite **bonifico** o **ricarica carta**.")
    st.divider()
    col1, col2 = st.columns([1, 2])
    col1.markdown("**👤 Intestatario**")
    col2.markdown("Andrea Scelzo")
    col1.markdown("**💳 N° Carta**")
    col2.code("5333 1759 3373 3088")
    col1.markdown("**🏦 IBAN**")
    col2.code("IT30 B360 8105 1382 9282 0692 842")
    st.divider()
    st.caption(
        "📌 Nessun codice fiscale richiesto online. "
        "Ricarica mensile automatica: attivabile dall'app Postepay / Poste Italiane. "
        "Bonifico gratuito da altra PostePay Evolution."
    )


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
if 'gps_rite' not in st.session_state:
    st.session_state.gps_rite = None
if 'gps_vesuvio' not in st.session_state:
    st.session_state.gps_vesuvio = None
if 'alert_level_cache' not in st.session_state:
    st.session_state.alert_level_cache = None
if 'bulletin_live_cache' not in st.session_state:
    st.session_state.bulletin_live_cache = None

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
        f"""<div style="background:rgba(255,255,255,0.08);padding:12px 14px;
border-radius:10px;border:1px solid #e8a800;margin-top:4px;">
<p style="color:#f1faee;font-size:11px;margin:0 0 8px 0;text-align:center;letter-spacing:.05em;">
☕ {_support}</p>
<a href="https://www.paypal.com/donate/?business=meteotorre@gmail.com" target="_blank"
style="display:block;text-align:center;background:linear-gradient(135deg,#f7971e,#ffd200);
padding:9px 14px;text-decoration:none;border-radius:8px;
box-shadow:0 3px 10px rgba(255,210,0,.4);">
<span style="color:#1a1a1a;font-size:14px;font-weight:800;letter-spacing:.03em;">☕ {_coffee}</span>
</a></div>""",
        unsafe_allow_html=True,
    )
    # CSS per uniformare il pulsante PostePay al riquadro giallo
    st.markdown(
        """<style>
div[data-testid="stSidebarContent"] div.stButton:last-of-type > button {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.35);
    color: #f1faee;
    font-weight: 700;
    font-size: 13px;
    width: 100%;
    border-radius: 8px;
    margin-top: 6px;
}
div[data-testid="stSidebarContent"] div.stButton:last-of-type > button:hover {
    background: rgba(255,255,255,0.16);
    border-color: #e8a800;
}
</style>""",
        unsafe_allow_html=True,
    )
    if st.button("💳 Dona con PostePay", key="btn_postepay", use_container_width=True):
        _show_postepay_dialog()

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
            try: st.session_state.bulletin_live_cache = _fbv.result()
            except Exception: pass
            try: st.session_state.alert_level_cache   = _fal.result()
            except Exception: pass
            try: st.session_state.gps_rite    = _fgps.result()
            except Exception: pass
            try: st.session_state.gps_vesuvio = _fgpsv.result()
            except Exception: pass
            for _fut in (_faq, _faqv, _fst):
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
    import ml_forecast_service
    st.header("🤖 Assistente AI Sismico")
    st.markdown(
        "Analisi avanzata basata su modelli AI/ML sui dati live INGV. "
        "**SISMAI** integra RandomForest + Poisson-G-R + Omori-Utsu con pressione atmosferica live. "
        "Include la ricerca INGV OV + Stanford (Science 2025)."
    )

    eq_data = st.session_state.earthquake_data
    from data_service import filter_area_earthquakes, fetch_earthquake_data_for_ml_area
    import ingv_monitor

    # Dati recenti (30gg) per conteggi display e badge
    cf_df  = filter_area_earthquakes(eq_data, "campi_flegrei") if eq_data is not None else None
    ves_df = filter_area_earthquakes(eq_data, "vesuvio")       if eq_data is not None else None
    isc_df = filter_area_earthquakes(eq_data, "ischia")        if eq_data is not None else None

    # Dati 90 giorni (box allargato, M≥0.0) per i modelli AI — sempre disponibili
    with st.spinner("⏳ Caricamento storico 90 giorni per modelli AI..."):
        cf_df90  = fetch_earthquake_data_for_ml_area("campi_flegrei", days=90)
        ves_df90 = fetch_earthquake_data_for_ml_area("vesuvio",       days=90)
        isc_df90 = fetch_earthquake_data_for_ml_area("ischia",        days=90)

    # Riusa i dati già caricati dal prefetch (session_state) — evita doppio fetch
    _static_bv    = ingv_monitor.get_ingv_bulletin_values()
    bulletin_live = st.session_state.bulletin_live_cache or ingv_monitor.fetch_bulletin_values_live()
    bulletin_cf   = bulletin_live.get("campi_flegrei", _static_bv.get("campi_flegrei", {}))
    bulletin_ves  = bulletin_live.get("vesuvio",       _static_bv.get("vesuvio", {}))
    alert         = st.session_state.alert_level_cache or ingv_monitor.fetch_ingv_alert_level() or {}
    gps           = st.session_state.gps_rite or ingv_monitor.fetch_gps_rite()
    gps_ves       = st.session_state.gps_vesuvio or {}

    # ── Funzione banner fonte dati per ogni tab ──────────────────────────────
    def _fonte_banner(df90, df30, area_label: str, fetch_ts=None):
        """Banner compatto che mostra: n eventi live, finestra, fonte, freshness."""
        n90  = len(df90)  if df90  is not None and not df90.empty  else 0
        n30  = len(df30)  if df30  is not None and not df30.empty  else 0
        ts   = fetch_ts or st.session_state.last_data_fetch
        ts_s = ts.strftime("%H:%M") if ts else "—"

        # GPS live o fallback
        if area_label == "Campi Flegrei":
            gps_val  = gps.get("uplift_mm_month") or gps.get("gps_uplift_mm_month")
            gps_src  = gps.get("source", "NGL/RITE")
            gps_live = bool(gps.get("_live") or gps.get("data_source") == "NGL")
        elif area_label == "Vesuvio":
            gps_val  = gps_ves.get("uplift_mm_month") or gps_ves.get("gps_uplift_mm_month")
            gps_src  = gps_ves.get("source", "NGL/Vesuvio")
            gps_live = bool(gps_ves.get("_live") or gps_ves.get("data_source") == "NGL")
        else:
            gps_val, gps_src, gps_live = None, None, False

        bl_scraped = bulletin_live.get("_scraped", False)
        _bl_map    = {"Campi Flegrei": bulletin_cf, "Vesuvio": bulletin_ves}
        _bl_cur    = _bl_map.get(area_label, bulletin_cf)
        bl_date    = _bl_cur.get("bulletin_date") or "—"
        alert_src  = alert.get("_source", "INGV OV") if alert else "INGV OV"

        # Componi badge
        def _b(txt, color):
            return (
                f"<span style='background:{color};color:#fff;border-radius:4px;"
                f"padding:1px 7px;font-size:11px;font-weight:700;margin:1px 2px;"
                f"display:inline-block;'>{txt}</span>"
            )
        seismic_b = _b(f"INGV LIVE  {n90}ev/90gg · {n30}ev/30gg · {ts_s}", "#198754")
        gps_b = (_b(f"GPS {gps_src}  {gps_val:+.1f} mm/mese", "#0d6efd" if gps_live else "#6c757d")
                 if gps_val is not None else "")
        alert_b = _b(f"Allerta INGV OV  {alert_src}", "#198754" if alert_src != "INGV OV" else "#fd7e14")
        bulletin_b = (
            _b(f"Bollettino INGV OV  {bl_date} (live)", "#198754")
            if bl_scraped else
            _b(f"Bollettino INGV OV  {bl_date} (fallback)", "#6c757d")
        )
        st.markdown(
            f"<div style='background:#f0f2f6;border-radius:8px;padding:8px 12px;"
            f"margin-bottom:10px;font-size:12px;'>"
            f"📡 <b>Sorgenti dati:</b> {seismic_b} {gps_b} {alert_b} {bulletin_b}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Carica dati AI per tutte le aree (usa 90gg per avere sempre abbastanza dati) ──
    with st.spinner("⏳ Modelli AI in esecuzione sui dati INGV..."):
        anomaly_cf  = ai_analysis.detect_anomalies(cf_df90,  "campi_flegrei") if cf_df90  is not None and not cf_df90.empty  else {}
        pattern_cf  = ai_analysis.classify_seismic_pattern(cf_df90,  "campi_flegrei") if cf_df90  is not None and not cf_df90.empty  else {}
        bvalue_cf   = ai_analysis.compute_gutenberg_richter(cf_df90,  "campi_flegrei") if cf_df90  is not None and not cf_df90.empty  else {}
        gps_corr_cf = ai_analysis.compute_gps_seismicity_correlation(cf_df90, gps)
        anomaly_ves = ai_analysis.detect_anomalies(ves_df90, "vesuvio")       if ves_df90 is not None and not ves_df90.empty else {}
        pattern_ves = ai_analysis.classify_seismic_pattern(ves_df90, "vesuvio")       if ves_df90 is not None and not ves_df90.empty else {}
        bvalue_ves  = ai_analysis.compute_gutenberg_richter(ves_df90, "vesuvio")       if ves_df90 is not None and not ves_df90.empty else {}
        anomaly_isc = ai_analysis.detect_anomalies(isc_df90, "ischia")        if isc_df90 is not None and not isc_df90.empty else {}
        pattern_isc = ai_analysis.classify_seismic_pattern(isc_df90, "ischia")        if isc_df90 is not None and not isc_df90.empty else {}
        bvalue_isc  = ai_analysis.compute_gutenberg_richter(isc_df90, "ischia")        if isc_df90 is not None and not isc_df90.empty else {}

    import multi_ai_service

    # ── Tab CF / Vesuvio / Ischia / SISMAI / Multi-AI / Ricerca / Chat ────────
    tab_cf, tab_ves, tab_isc, tab_sismai, tab_multiAI, tab_ingv, tab_chat = st.tabs(
        ["🔴 Campi Flegrei", "🌋 Vesuvio", "🏝️ Ischia",
         "🔮 SISMAI", "🧠 Multi-AI", "🔬 Ricerca INGV AI", "🤖 Chat AI"]
    )

    with tab_cf:
        st.markdown("### Analisi AI — Campi Flegrei")
        _fonte_banner(cf_df90, cf_df, "Campi Flegrei")
        if cf_df90 is None or cf_df90.empty:
            st.warning("Nessun dato sismico disponibile per i Campi Flegrei.")
        else:
            _render_ai_panel(anomaly_cf, pattern_cf, bvalue_cf, gps_corr_cf)

    with tab_ves:
        st.markdown("### Analisi AI — Vesuvio")
        _fonte_banner(ves_df90, ves_df, "Vesuvio")
        if ves_df90 is None or ves_df90.empty:
            st.success("✅ Nessuna attività sismica rilevante. Attività nella norma (VERDE).")
        else:
            _render_ai_panel(anomaly_ves, pattern_ves, bvalue_ves, None)

    with tab_isc:
        st.markdown("### Analisi AI — Ischia")
        _fonte_banner(isc_df90, isc_df, "Ischia")
        st.info(
            "🏝️ **Nota Ischia**: La sismicità è prevalentemente tettonica superficiale (<5 km). "
            "L'anomaly detection e il b-value sono utili per identificare "
            "sequenze precursori di eventi come quello del 2022 (M 5.7)."
        )
        if isc_df90 is None or isc_df90.empty:
            st.success("✅ Nessun evento sismico recente nell'area di Ischia — attività nella norma.")
        else:
            _render_ai_panel(anomaly_isc, pattern_isc, bvalue_isc, None)

    # ── SISMAI ────────────────────────────────────────────────────────────────
    with tab_sismai:
        st.markdown("### ©️ SISMAI — Sistema Integrato Sismico Multi-AI")
        st.markdown(
            "Modello ensemble **RandomForest + Poisson-Gutenberg-Richter + Omori-Utsu** "
            "con feature live: sismicità INGV/GOSSIP-OV/EMSC · pressione atmosferica (base+vetta) · "
            "temperatura · bollettino INGV OV · GPS deformazione · 90 giorni di storico."
        )

        sismai_area = st.selectbox(
            "Area di previsione SISMAI",
            ["Campi Flegrei", "Vesuvio", "Ischia"],
            key="sismai_area_sel",
        )
        # Usa 90 giorni (box allargato) per SISMAI
        sismai_df_map = {
            "Campi Flegrei": cf_df90,
            "Vesuvio":       ves_df90,
            "Ischia":        isc_df90,
        }
        sismai_df = sismai_df_map.get(sismai_area)

        if sismai_df is None or sismai_df.empty:
            st.warning(f"⚠️ Nessun dato sismico disponibile per la previsione ({sismai_area}).")
        else:
            with st.spinner(f"🔮 SISMAI in esecuzione per {sismai_area}..."):
                atm = ml_forecast_service.fetch_atmospheric_features(sismai_area)
                fc  = ml_forecast_service.run_ml_forecast(
                    sismai_df, area=sismai_area, horizon=7,
                    with_ai_narrative=True, atm=atm,
                )

            if fc.get("error"):
                st.warning(f"⚠️ {fc['error']}")
            else:
                # ── BADGE SORGENTI DATI ────────────────────────────────────
                atm_data   = fc.get("atm", {})
                p_base     = atm_data.get("pressure_base", 0.0)
                p_vetta    = atm_data.get("pressure_vetta", None)
                p_delta    = atm_data.get("pressure_delta", 0.0)
                temp_b     = atm_data.get("temp_base", 0.0)
                temp_v     = atm_data.get("temp_vetta", None)

                # Determina sorgenti live dal dataframe SISMAI
                _src_active = set(sismai_df["source"].unique()) if "source" in sismai_df.columns else set()
                _meteo_live = abs(p_base - 1013.25) > 0.5  # Open-Meteo ha risposto se diverso dal default

                def _src_badge(name: str, is_live: bool, n: int = 0) -> str:
                    color  = "#198754" if is_live else "#adb5bd"
                    status = "LIVE" if is_live else "fallback"
                    count  = f" ({n})" if n > 0 else ""
                    return (
                        f"<span style='display:inline-block;background:{color};color:#fff;"
                        f"border-radius:5px;padding:2px 8px;font-size:11px;font-weight:700;"
                        f"margin:2px 3px;'>{name} {status}{count}</span>"
                    )

                def _n(src: str) -> int:
                    return int(sismai_df[sismai_df["source"] == src].shape[0]) if src in _src_active else 0

                badges_html = (
                    "<div style='margin-bottom:8px;'>"
                    + _src_badge("INGV", "INGV" in _src_active, _n("INGV"))
                    + _src_badge("GOSSIP-OV", "GOSSIP-OV" in _src_active, _n("GOSSIP-OV"))
                    + _src_badge("EMSC", "EMSC" in _src_active, _n("EMSC"))
                    + _src_badge("Open-Meteo", _meteo_live)
                    + _src_badge("Bollettino OV", bool((st.session_state.get("bulletin_live_cache") or {}).get("_scraped")))
                    + "</div>"
                )
                st.markdown(
                    f"<div style='background:#f8f9fa;border-radius:8px;padding:10px 14px;"
                    f"margin-bottom:12px;border:1px solid #dee2e6;'>"
                    f"<span style='font-size:12px;font-weight:600;color:#555;'>📡 Sorgenti dati attive:</span><br>"
                    f"{badges_html}</div>",
                    unsafe_allow_html=True,
                )

                # ── DATI METEOROLOGICI ─────────────────────────────────────
                st.markdown("#### 🌡️ Dati meteorologici live (feature SISMAI)")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric(
                    "Pressione base",
                    f"{p_base:.1f} hPa",
                    delta=None if not _meteo_live else "🟢 live",
                )
                m2.metric("Δ Pressione base-vetta", f"{p_delta:+.1f} hPa")
                m3.metric(
                    "Temp. base",
                    f"{temp_b:.1f} °C",
                    delta=None if not _meteo_live else "🟢 live",
                )
                if temp_v is not None:
                    m4.metric("Temp. vetta", f"{temp_v:.1f} °C", delta="🟢 live")
                else:
                    m4.metric("Temp. vetta", "formula", delta="📐 adiabatica")
                m5.metric("Fonte meteo", "Open-Meteo" if _meteo_live else "⚠️ fallback")

                # ── PREVISIONE 7 GIORNI ────────────────────────────────────
                st.markdown("#### 🔮 Previsione rischio sismico — prossimi 7 giorni")
                cols_fc = st.columns(7)
                days = fc.get("days", [])
                for i, day in enumerate(days[:7]):
                    with cols_fc[i]:
                        date_str = str(day["date"])[-5:]
                        color = day["color"]
                        label = day["label"]
                        conf  = day["confidence"]
                        st.markdown(
                            f"""<div style="text-align:center;border:2px solid {color};
border-radius:10px;padding:10px 4px;background:#fff;">
<div style="font-size:11px;color:#666;">{date_str}</div>
<div style="font-size:17px;font-weight:800;color:{color};">{label}</div>
<div style="font-size:11px;color:#888;">{conf*100:.0f}%</div>
</div>""",
                            unsafe_allow_html=True,
                        )

                # ── PARAMETRI MODELLO ──────────────────────────────────────
                st.markdown("#### 📊 Parametri modello ensemble RF+GB+Poisson")
                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                mc1.metric("Accuratezza CV", f"{fc.get('cv_score',0)*100:.1f}%")
                mc2.metric("Peso RandomForest", f"{fc.get('weight_rf',0)*100:.0f}%")
                mc3.metric("Peso GradBoost", f"{fc.get('weight_gb',0)*100:.0f}%")
                mc4.metric("Peso Poisson-GR", f"{fc.get('weight_poisson',0)*100:.0f}%")
                mc5.metric("Giorni training", f"{fc.get('n_train',0)}")

                # ── TOP FEATURE ────────────────────────────────────────────
                top_feats = fc.get("top_features", [])
                if top_feats:
                    st.markdown("#### 🏆 Feature più importanti nel modello")
                    feat_labels = {
                        "n_7d": "Sismicità 7gg", "n_3d": "Sismicità 3gg",
                        "n_14d": "Sismicità 14gg", "energy_7d": "Energia 7gg",
                        "maxmag_7d": "Mag max 7gg", "days_since_sig": "Giorni da M≥3",
                        "pressure_base": "Pressione base", "pressure_delta": "Δ Pressione",
                        "temp_base": "Temp. base", "temp_vetta": "Temp. vetta",
                        "log_energy": "Log energia",
                    }
                    feat_cols = st.columns(min(len(top_feats), 5))
                    for i, (fname, fval) in enumerate(top_feats[:5]):
                        with feat_cols[i]:
                            st.metric(feat_labels.get(fname, fname.replace("_", " ")), f"{fval*100:.1f}%")

                # ── NARRATIVA AI ───────────────────────────────────────────
                narrative = fc.get("ai_narrative", "")
                if narrative:
                    st.markdown("#### 💬 Analisi AI del forecast")
                    st.info(narrative)

                st.caption(
                    "⚠️ SISMAI è un sistema statistico sperimentale. "
                    "Non sostituisce i comunicati ufficiali INGV/DPC. "
                    "Nessun sistema può prevedere i terremoti con certezza."
                )

    # ── MULTI-AI CONSENSUS ────────────────────────────────────────────────────
    with tab_multiAI:
        st.markdown("### 🧠 Analisi Multi-AI — Consenso GPT + Claude + Gemini")
        st.markdown(
            "Interroga in parallelo **OpenAI GPT-5**, **Anthropic Claude** e **Google Gemini** "
            "con lo stesso contesto sismico live. Genera un consenso scientifico da 3 AI distinte."
        )

        prov_status = multi_ai_service.providers_status()
        pc1, pc2, pc3 = st.columns(3)
        for col, (key, info) in zip([pc1, pc2, pc3], prov_status.items()):
            icon = "🟢" if info["available"] else "🔴"
            with col:
                st.markdown(
                    f"<div style='text-align:center;padding:8px;border:1px solid #ddd;"
                    f"border-radius:8px;font-size:13px;'>{icon} <b>{info['model']}</b></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        mai_area = st.selectbox(
            "Area di analisi Multi-AI",
            ["Campi Flegrei", "Vesuvio", "Ischia"],
            key="multi_ai_area_sel",
        )

        _df90_map = {"Campi Flegrei": cf_df90, "Vesuvio": ves_df90, "Ischia": isc_df90}

        # GPS live: usa NGL/RITE per CF, NGL/Vesuvio per Vesuvio (session_state-backed)
        def _live_gps_uplift(area_key: str) -> float:
            if area_key == "Campi Flegrei":
                v = (gps.get("uplift_mm_month") or gps.get("gps_uplift_mm_month")
                     or bulletin_cf.get("gps_uplift_mm_month", 0.0))
            elif area_key == "Vesuvio":
                v = (gps_ves.get("uplift_mm_month") or gps_ves.get("gps_uplift_mm_month")
                     or bulletin_ves.get("gps_uplift_mm_month", 0.0))
            else:
                v = 0.0
            return float(v or 0.0)

        _alert_map = {
            "Campi Flegrei": (alert or {}).get("campi_flegrei") or bulletin_cf.get("alert_level", "GIALLO"),
            "Vesuvio":       (alert or {}).get("vesuvio")       or bulletin_ves.get("alert_level", "VERDE"),
            "Ischia":        "VERDE",
        }

        mai_df = _df90_map.get(mai_area)
        n_events_mai  = len(mai_df) if mai_df is not None and not mai_df.empty else 0
        max_mag_mai   = float(mai_df["magnitude"].max())  if n_events_mai > 0 else 0.0
        avg_mag_mai   = float(mai_df["magnitude"].mean()) if n_events_mai > 0 else 0.0
        emsc_n_mai    = int(mai_df[mai_df["source"] == "EMSC"].shape[0]) if (
            mai_df is not None and not mai_df.empty and "source" in mai_df.columns) else 0

        if st.button(f"🚀 Avvia analisi Multi-AI per {mai_area}", type="primary", key="btn_multi_ai"):
            with st.spinner("🧠 Calcolo SISMAI + interrogazione GPT-5 · Claude · Gemini in parallelo..."):
                atm_live = ml_forecast_service.fetch_atmospheric_features(mai_area)

                # Pre-calcola SISMAI per avere il forecast label reale
                sismai_label = "BASSO"
                if mai_df is not None and not mai_df.empty:
                    try:
                        _fc_pre = ml_forecast_service.run_ml_forecast(
                            mai_df, area=mai_area, horizon=1, with_ai_narrative=False, atm=atm_live
                        )
                        if _fc_pre and not _fc_pre.get("error") and _fc_pre.get("days"):
                            sismai_label = _fc_pre["days"][0]["label"]
                    except Exception:
                        pass

                data_ctx = {
                    "n_events":             n_events_mai,
                    "max_mag":              max_mag_mai,
                    "avg_mag":              avg_mag_mai,
                    "alert_level":          _alert_map.get(mai_area, "VERDE"),
                    "gps_uplift_mm_month":  _live_gps_uplift(mai_area),
                    "pressure_base":        atm_live.get("pressure_base", 1013.0),
                    "temp_base":            atm_live.get("temp_base", 15.0),
                    "temp_vetta":           atm_live.get("temp_vetta"),
                    "sismai_forecast_label": sismai_label,
                    "emsc_n_events":        emsc_n_mai,
                    "isc_n_events":         0,
                    "period_days":          90,
                }
                mai_result = multi_ai_service.multi_ai_consensus(mai_area, data_ctx)

            st.success(f"✅ Analisi completata in {mai_result['elapsed_s']}s")

            st.markdown("#### 📊 Contesto dati inviato ai 3 AI")
            with st.expander("Vedi prompt inviato"):
                st.code(mai_result.get("prompt", ""), language=None)

            st.markdown("#### 🤖 Risposte individuali")
            col_g, col_c, col_gem = st.columns(3)

            with col_g:
                st.markdown(
                    "<div style='background:#e8f4fd;border-radius:10px;padding:14px;"
                    "border-left:4px solid #0d6efd;'>"
                    "<b style='color:#0d6efd;'>🔵 GPT-5 (OpenAI)</b></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(mai_result.get("gpt") or "_Non disponibile_")

            with col_c:
                st.markdown(
                    "<div style='background:#fdf0e8;border-radius:10px;padding:14px;"
                    "border-left:4px solid #fd7e14;'>"
                    "<b style='color:#fd7e14;'>🟠 Claude (Anthropic)</b></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(mai_result.get("claude") or "_Non disponibile_")

            with col_gem:
                st.markdown(
                    "<div style='background:#e8fdf0;border-radius:10px;padding:14px;"
                    "border-left:4px solid #198754;'>"
                    "<b style='color:#198754;'>🟢 Gemini (Google)</b></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(mai_result.get("gemini") or "_Non disponibile_")

            st.markdown("---")
            st.markdown("#### 🎯 Consenso Scientifico Multi-AI")
            consensus = mai_result.get("consensus") or "Consenso non disponibile."
            st.markdown(
                f"<div style='background:linear-gradient(135deg,#f8f0ff 0%,#fff 100%);"
                f"border:2px solid #6f42c1;border-radius:12px;padding:20px;"
                f"font-size:15px;line-height:1.7;color:#333;'>"
                f"<b style='color:#6f42c1;'>🧠 Sintesi consensuale (GPT-5 su 3 pareri):</b><br><br>"
                f"{consensus}</div>",
                unsafe_allow_html=True,
            )
            st.caption(
                f"Analisi generata il {mai_result.get('timestamp','—')} · "
                f"Dati: INGV/GOSSIP-OV/EMSC · AI: OpenAI + Anthropic + Google · "
                f"Nessuna risposta è una previsione scientifica certificata."
            )
        else:
            st.info(
                "💡 Premi **Avvia analisi Multi-AI** per interrogare i 3 sistemi AI con i dati "
                "sismici live dell'area selezionata. La risposta arriva in ~10-20 secondi."
            )

    # ── Ricerca INGV AI ───────────────────────────────────────────────────────
    with tab_ingv:
        st.markdown("### 🔬 Ricerca AI per la Sismologia — INGV OV + Stanford")

        # Card principale research
        st.markdown("""
<div style="border:2px solid #0d6efd;border-radius:14px;padding:24px;margin-bottom:20px;
background:linear-gradient(135deg,#f0f4ff 0%,#fff 100%);">
<div style="font-size:13px;font-weight:700;color:#0d6efd;letter-spacing:.08em;
text-transform:uppercase;margin-bottom:10px;">
📰 Studio pubblicato su Science — Aprile 2025
</div>
<div style="font-size:20px;font-weight:800;color:#1a1a2e;margin-bottom:12px;line-height:1.3;">
Intelligenza Artificiale per il Monitoraggio della Sismicità ai Campi Flegrei
</div>
<div style="font-size:14px;color:#333;line-height:1.7;">
<b>Collaborazione internazionale:</b> Doer School of Sustainability – Stanford University &nbsp;·&nbsp;
INGV Osservatorio Vesuviano (Napoli) &nbsp;·&nbsp; Università degli Studi di Napoli Federico II
<br><br>
L'AI ha analizzato le tracce sismiche registrate <b>dal 2022 a marzo 2025</b> dalla fitta rete
sismica dell'Osservatorio Vesuviano, identificando i terremoti che caratterizzano l'attuale
<i>unrest</i> vulcanico dei Campi Flegrei.
</div>
</div>
""", unsafe_allow_html=True)

        # Risultati chiave
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("""
<div style="border:2px solid #198754;border-radius:12px;padding:18px;height:100%;background:#fff;">
<div style="font-size:13px;font-weight:700;color:#198754;text-transform:uppercase;margin-bottom:8px;">
🔍 Risultati principali
</div>
<ul style="font-size:14px;color:#333;line-height:1.9;margin:0;padding-left:18px;">
<li>Rilevati e localizzati oltre <b>54.000 terremoti nascosti</b> nel rumore sismico</li>
<li>La maggior parte di magnitudo molto bassa, <b>mai catalogati</b> prima</li>
<li>La caldera dei Campi Flegrei è in <i>unrest</i> dal 2005, con forte aumento recente di sismicità,
sollevamento del suolo e attività fumarolica</li>
<li>Definite le <b>faglie che delimitano la zona di sollevamento</b> nella caldera</li>
<li>Mappato il sistema di faglie superficiali nella <b>zona idrotermale</b> di Solfatara/Pisciarelli</li>
</ul>
</div>
""", unsafe_allow_html=True)

        with col_r2:
            st.markdown("""
<div style="border:2px solid #fd7e14;border-radius:12px;padding:18px;height:100%;background:#fff;">
<div style="font-size:13px;font-weight:700;color:#fd7e14;text-transform:uppercase;margin-bottom:8px;">
🤖 Software AI in sviluppo all'OV
</div>
<ul style="font-size:14px;color:#333;line-height:1.9;margin:0;padding-left:18px;">
<li>Software sviluppato all'Università di Stanford, istruito sul <b>catalogo sismico OV
dal 2000 ad oggi</b>, costantemente aggiornato</li>
<li>Permette di <b>identificare e localizzare terremoti in tempo quasi-reale</b> (near real-time)</li>
<li>Consente di seguire l'evoluzione della sismicità in maniera <b>automatica</b></li>
<li>Attualmente <b>in fase di test</b> presso l'Osservatorio Vesuviano</li>
<li>Strumento fondamentale per la <b>mitigazione del rischio</b> ai Campi Flegrei</li>
</ul>
</div>
""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Confronto con SISMAI
        st.markdown("""
<div style="border:2px solid #6f42c1;border-radius:12px;padding:18px;margin-bottom:16px;background:#fff;">
<div style="font-size:13px;font-weight:700;color:#6f42c1;text-transform:uppercase;margin-bottom:8px;">
🔮 SISMAI in questa app — approccio complementare
</div>
<div style="font-size:14px;color:#333;line-height:1.7;">
Mentre il sistema INGV/Stanford si concentra sull'<b>identificazione di eventi nascosti nel rumore
sismico</b> (machine learning su segnali raw), <b>SISMAI</b> usa i cataloghi INGV/GOSSIP-OV/EMSC già filtrati
per fare <b>previsioni probabilistiche del rischio</b> nei 7 giorni successivi, integrando:
<br><br>
<b>RandomForest</b> (feature temporali sismiche) &nbsp;+&nbsp;
<b>Poisson-Gutenberg-Richter</b> (statistica frequenza-magnitudo) &nbsp;+&nbsp;
<b>Omori-Utsu</b> (decadimento aftershock) &nbsp;+&nbsp;
<b>Pressione atmosferica live</b> (base+vetta, Open-Meteo) &nbsp;+&nbsp;
<b>GPS deformazione</b> (RITE/NGL) &nbsp;+&nbsp;
<b>Bollettino INGV OV</b> (CO₂, fumarole, radon)
</div>
</div>
""", unsafe_allow_html=True)

        # Link
        st.markdown("#### 🔗 Risorse ufficiali")
        lc1, lc2, lc3 = st.columns(3)
        _yr = datetime.now().year
        with lc1:
            st.link_button(
                "🌋 Stato Attuale CF — INGV OV",
                "https://www.ov.ingv.it/index.php/monitoraggio-sismico-e-vulcanico/campi-flegrei/campi-flegrei-attivita-recente",
                use_container_width=True,
            )
        with lc2:
            st.link_button(
                "📡 Bollettini Settimanali CF",
                f"https://www.ov.ingv.it/index.php/monitoraggio-e-infrastrutture/bollettini-tutti/boll-sett-flegre/anno-{_yr}",
                use_container_width=True,
            )
        with lc3:
            st.link_button(
                "🌐 INGV Osservatorio Vesuviano",
                "https://www.ov.ingv.it/",
                use_container_width=True,
            )

        st.caption(
            "Fonte: INGV Osservatorio Vesuviano · Stanford Doer School of Sustainability · "
            "Università degli Studi di Napoli Federico II · Science (2025)"
        )

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

