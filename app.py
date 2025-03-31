import os
import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd

import data_service
import visualization
import emergency_info
import forum
import utils

# Configure page settings
st.set_page_config(
    page_title="Monitoraggio Sismico - Campania",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ScelzoF/SeismicSafetyItalia/issues',
        'Report a bug': 'https://github.com/ScelzoF/SeismicSafetyItalia/issues',
        'About': '### Monitoraggio Sismico - Campania\nSviluppato da Fabio SCELZO'
    }
)

# Carica stile CSS personalizzato
css_path = os.path.join(os.path.dirname(__file__), 'streamlit', 'style.css')
with open(css_path) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state variables if they don't exist
st.session_state.language = 'it'
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

# Translation dictionary
translations = {
    'it': {
        'title': 'Monitoraggio Sismico Real Time',
        'subtitle': 'Dati sismici in tempo reale nelle zone della Solfatara di Pozzuoli, Vesuvio ed Italia in generale',
        'language': 'Lingua',
        'monitoring': 'Monitoraggio',
        'predictions': 'Previsioni',
        'emergency': 'Emergenza',
        'community': 'Comunità',
        'about': 'Informazioni',
        'last_update': 'Ultimo aggiornamento',
        'updating': 'Aggiornamento in corso...',
        'enable_notifications': 'Abilita notifiche',
        'refresh': 'Aggiorna dati',
        'recent_earthquakes': 'Terremoti Recenti',
        'magnitude': 'Magnitudo',
        'depth': 'Profondità',
        'location': 'Località',
        'time': 'Ora',
        'no_data': 'Nessun dato disponibile',
        'data_source': 'Fonte dati: INGV e USGS',
        'debug_mode': 'Modalità sviluppatore',
        'debug_info': 'Informazioni di debug',
        'debug_section': 'Sezione di debug',
        'api_status': 'Stato API',
        'data_stats': 'Statistiche dati',
        'close': 'Chiudi',
        'seismic_activity': 'Attività sismica'
    }
}

# Function to get translated text
def get_text(key):
    return translations[st.session_state.language][key]

# Sidebar for navigation and settings
with st.sidebar:
    st.title("🌋 " + get_text('title'))
    
    # Language selector
    lang_options = {'it': 'Italiano'}
    selected_lang = st.selectbox(
        get_text('language'),
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(st.session_state.language)
    )
    
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
    
    # Navigation menu
    st.header("📋 Menu")
    page = st.radio(
        "Navigation",
        ["monitoring", "predictions", "emergency", "community", "about"],
        format_func=lambda x: get_text(x),
        label_visibility="collapsed"
    )
    
    # Notification toggle
    st.checkbox(
        get_text('enable_notifications'),
        value=st.session_state.notification_enabled,
        key="notification_toggle",
        on_change=utils.toggle_notifications
    )
    
    # Refresh data button
    if st.button(get_text('refresh')):
        with st.spinner(get_text('updating')):
            st.session_state.earthquake_data = data_service.fetch_earthquake_data()
            st.session_state.last_data_fetch = datetime.now()
            st.rerun()
    
    # Last update timestamp
    if st.session_state.last_data_fetch:
        st.info(f"{get_text('last_update')}: {st.session_state.last_data_fetch.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Data source attribution
    st.caption(get_text('data_source'))
    
    # Sezione donazione PayPal
    st.markdown("---")
    st.markdown("### 💖 Supporta il progetto")
    st.markdown("[☕ Fai una donazione su PayPal](https://www.paypal.com/donate/?business=meteotorre@gmail.com)")

# Main content area
st.title("🌋 " + get_text('title'))
st.subheader(get_text('subtitle'))

# Check if we need to fetch data
if st.session_state.earthquake_data is None or (
    st.session_state.last_data_fetch and 
    datetime.now() - st.session_state.last_data_fetch > timedelta(minutes=15)
):
    with st.spinner(get_text('updating')):
        st.session_state.earthquake_data = data_service.fetch_earthquake_data()
        st.session_state.last_data_fetch = datetime.now()

# Display the selected page content
if page == "monitoring":
    visualization.show_monitoring_page(st.session_state.earthquake_data, get_text)
elif page == "predictions":
    visualization.show_predictions_page(st.session_state.earthquake_data, get_text)
elif page == "emergency":
    emergency_info.show_emergency_page(get_text)
elif page == "community":
    forum.main()
elif page == "about":
    utils.show_about_page(get_text)

# Check for significant earthquakes and show alert if notifications are enabled
if st.session_state.notification_enabled and st.session_state.earthquake_data is not None:
    significant_eq = data_service.get_significant_earthquakes(st.session_state.earthquake_data)
    if not significant_eq.empty:
        for _, eq in significant_eq.iterrows():
            st.toast(f"⚠️ {get_text('magnitude')}: {eq['magnitude']} - {eq['location']}")

# Import the process_data function from monitoraggio
from monitoraggio import process_data

# Call the process_data function to display seismic monitoring data
def main():
    process_data()

if __name__ == "__main__":
    main()

# Aggiungiamo la visualizzazione del meteo
import meteo

# Chiamata alla funzione show per mostrare la sezione meteo
meteo.show()
