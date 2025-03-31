import os
import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup

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
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'last_weather_fetch' not in st.session_state:
    st.session_state.last_weather_fetch = None

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
        'seismic_activity': 'Attività sismica',
        'weather': 'Meteo',
        'weather_forecast': 'Previsioni Meteo',
        'temp': 'Temperatura',
        'humidity': 'Umidità',
        'wind': 'Vento',
        'condition': 'Condizione'
    }
}

# Function to get translated text
def get_text(key):
    return translations[st.session_state.language][key]

# Funzione per ottenere dati meteo aggiornati da ilMeteo.it (esempio con HTML parsing)
def fetch_weather_data():
    try:
        # Puoi sostituire questa URL con la località specifica di Torre Annunziata
        url = "https://www.ilmeteo.it/meteo/Torre-Annunziata"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Questi selettori dovrebbero essere aggiornati in base alla struttura del sito
            current_temp = soup.select_one('.valoreTemp')
            current_condition = soup.select_one('.condizione')
            humidity = soup.select_one('.umidita')
            wind = soup.select_one('.vento')
            
            # Previsioni per i prossimi giorni (esempio)
            forecast_days = soup.select('.boxprevisione')
            forecast = []
            
            for day in forecast_days[:3]:  # Prendi solo i primi 3 giorni
                day_name = day.select_one('.giorno')
                max_temp = day.select_one('.temp-max')
                min_temp = day.select_one('.temp-min')
                day_condition = day.select_one('.condizione')
                
                if day_name and max_temp and min_temp and day_condition:
                    forecast.append({
                        'day': day_name.text.strip(),
                        'max_temp': max_temp.text.strip(),
                        'min_temp': min_temp.text.strip(),
                        'condition': day_condition.text.strip()
                    })
            
            return {
                'current': {
                    'temp': current_temp.text.strip() if current_temp else "N/A",
                    'condition': current_condition.text.strip() if current_condition else "N/A",
                    'humidity': humidity.text.strip() if humidity else "N/A",
                    'wind': wind.text.strip() if wind else "N/A"
                },
                'forecast': forecast
            }
        return None
    except Exception as e:
        st.error(f"Errore nel recupero dei dati meteo: {e}")
        return None

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
            
            # Aggiorna anche i dati meteo
            st.session_state.weather_data = fetch_weather_data()
            st.session_state.last_weather_fetch = datetime.now()
            
            st.rerun()
    
    # Last update timestamp
    if st.session_state.last_data_fetch:
        st.info(f"{get_text('last_update')}: {st.session_state.last_data_fetch.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Data source attribution
    st.caption(get_text('data_source'))
    
    # Sezione donazione PayPal abbellita
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #0070ba;">
        <h3 style="color: #0070ba; margin-top: 0;">💖 Sostieni il Progetto</h3>
        <p style="margin-bottom: 10px;">Se trovi utile questa applicazione, considera una piccola donazione per mantenere il servizio attivo e migliorarlo costantemente.</p>
        <a href="https://www.paypal.com/donate/?business=meteotorre@gmail.com" style="display: inline-block; background-color: #0070ba; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold;">
            ☕ Offrimi un caffè su PayPal
        </a>
    </div>
    """, unsafe_allow_html=True)

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
    
    # Aggiungiamo widget meteo
    st.subheader("🌤️ " + get_text('weather'))
    
    # Fetch weather data if not available or outdated
    if st.session_state.weather_data is None or (
        st.session_state.last_weather_fetch and 
        datetime.now() - st.session_state.last_weather_fetch > timedelta(hours=1)
    ):
        with st.spinner("Aggiornamento dati meteo..."):
            st.session_state.weather_data = fetch_weather_data()
            st.session_state.last_weather_fetch = datetime.now()
    
    # Display weather data
    if st.session_state.weather_data:
        current = st.session_state.weather_data['current']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Temperatura", current['temp'])
        
        with col2:
            st.metric("Condizione", current['condition'])
            
        with col3:
            st.metric("Umidità", current['humidity'])
            
        with col4:
            st.metric("Vento", current['wind'])
        
        # Previsioni future
        if st.session_state.weather_data['forecast']:
            st.subheader("Previsioni per i prossimi giorni")
            forecast_cols = st.columns(len(st.session_state.weather_data['forecast']))
            
            for i, day_forecast in enumerate(st.session_state.weather_data['forecast']):
                with forecast_cols[i]:
                    st.markdown(f"**{day_forecast['day']}**")
                    st.markdown(f"Max: {day_forecast['max_temp']}")
                    st.markdown(f"Min: {day_forecast['min_temp']}")
                    st.markdown(f"{day_forecast['condition']}")
    else:
        st.info("Dati meteo non disponibili al momento.")
    
    st.caption("Dati meteo forniti da ilMeteo.it")
        
elif page == "predictions":
    visualization.show_predictions_page(st.session_state.earthquake_data, get_text)
elif page == "emergency":
    emergency_info.show_emergency_page(get_text)
elif page == "community":
    forum.main()
elif page == "about":
    # Modifica qui per la sezione about
    st.header("ℹ️ Informazioni sul Progetto")
    
    st.subheader("🌋 Monitoraggio Sismico - Campania")
    st.markdown("""
    Un'applicazione per il monitoraggio in tempo reale dell'attività sismica nella regione Campania, 
    con particolare attenzione alle aree del Vesuvio e dei Campi Flegrei.
    """)
    
    st.markdown("---")
    
    # Sezione sullo sviluppatore
    st.subheader("👨‍💻 Lo Sviluppatore")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Caricamento diretto dell'immagine base64 (l'immagine caricata dall'utente)
        st.markdown("""
        <div style="text-align: center;">
            <img src="https://ljrjaehrttxhqejcueqj.supabase.co/storage/v1/object/public/immagini/fabio.jpg" width="200">
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### Fabio Scelzo
        
        Nato nel 1973, Fabio ha coltivato sin dall'infanzia una profonda passione per l'elettronica e l'informatica, 
        che è rimasta costante attraverso gli anni, evolvendo insieme alle tecnologie.
        
        Esperto di sviluppo software e appassionato di monitoraggio ambientale, ha creato questa piattaforma per 
        fornire uno strumento utile alla comunità, combinando competenze tecniche e interesse per il territorio.
        
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
    
    st.markdown("""
    ### Contatti
    
    📧 Email: meteotorre@gmail.com
    """)

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

# Rimuoviamo la chiamata al meteo originale poiché l'abbiamo integrato
# import meteo
# meteo.show()