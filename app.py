
import streamlit as st
from seo_tools import inject_meta_tags, show_robots_txt, show_sitemap_xml

# Iniettiamo meta tag all'avvio
inject_meta_tags()

# Controlla se è una richiesta SEO (robots.txt o sitemap.xml)
page = st.query_params.get("page", [None])[0]
if page == "robots":
    show_robots_txt()
    st.stop()
elif page == "sitemap":
    show_sitemap_xml()
    st.stop()


import os
import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd
import requests
import locale

import data_service
import visualization
import emergency_info
import forum
import utils

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
    initial_sidebar_state="expanded",
    menu_items={
        'About': '### Monitoraggio Sismico - Campania\nSviluppato da Fabio SCELZO'
    }
)

import orario
ora = orario.get_orario()
st.sidebar.write(f"UTC: {ora['utc']}")
st.sidebar.write(f"Italia: {ora['italia']} ({ora['diff']})")

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
        'condition': 'Condizione',
        'temp_max': 'Max',
        'temp_min': 'Min',
        'feels_like': 'Percepita',
        'pressure': 'Pressione',
        'clouds': 'Nuvolosità',
        'sunrise': 'Alba',
        'sunset': 'Tramonto'
    }
}

# Function to get translated text
def get_text(key):
    return translations[st.session_state.language][key]

# Funzione per tradurre i nomi dei giorni in italiano
def traduci_giorno(giorno_en):
    return giorni_settimana.get(giorno_en, giorno_en)

# Funzione per ottenere dati meteo da OpenWeather API
def fetch_weather_data():
    try:
        # Configurazione OpenWeather
        API_KEY = "d23fb9868855e4bcb4dcf04404d14a78"
        CITY = "Torre Annunziata"
        COUNTRY_CODE = "IT"
        LANG = "it"  # Lingua italiana per le descrizioni
        
        # Richiesta dati meteo attuali
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY},{COUNTRY_CODE}&appid={API_KEY}&units=metric&lang={LANG}"
        response = requests.get(current_url)
        
        if response.status_code != 200:
            # Se la richiesta fallisce, utilizziamo dati simulati
            return get_mock_weather_data()
            
        current_data = response.json()
        
        # Formattazione dati attuali
        current = {
            'temp': f"{current_data['main']['temp']:.1f}°C",
            'feels_like': f"{current_data['main']['feels_like']:.1f}°C",
            'humidity': f"{current_data['main']['humidity']}%",
            'pressure': f"{current_data['main']['pressure']} hPa",
            'wind': f"{current_data['wind']['speed']} m/s",
            'condition': current_data['weather'][0]['description'].capitalize(),
            'icon': current_data['weather'][0]['icon'],
            'clouds': f"{current_data['clouds']['all']}%",
            'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M'),
            'sunset': datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M')
        }
        
        # Richiesta previsioni per 5 giorni
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY},{COUNTRY_CODE}&appid={API_KEY}&units=metric&lang={LANG}"
        forecast_response = requests.get(forecast_url)
        
        if forecast_response.status_code != 200:
            # Se la richiesta fallisce, usiamo solo i dati attuali e previsioni simulate
            mock_data = get_mock_weather_data()
            return {'current': current, 'forecast': mock_data['forecast']}
            
        forecast_data = forecast_response.json()
        
        # Estrai dati per i prossimi giorni (uno per giorno, non ogni 3 ore)
        forecast = []
        days_processed = set()
        
        for item in forecast_data['list']:
            date = datetime.fromtimestamp(item['dt'])
            day_str = date.strftime('%Y-%m-%d')
            
            # Prendi solo un item per giorno (mezzogiorno)
            if day_str not in days_processed and date.hour >= 12 and date.hour <= 15:
                days_processed.add(day_str)
                
                # Se abbiamo già 5 giorni, fermiamoci
                if len(forecast) >= 5:
                    break
                
                # Ottieni il nome del giorno in inglese e traducilo in italiano
                day_name_en = date.strftime('%A')
                day_name_it = traduci_giorno(day_name_en)
                    
                forecast.append({
                    'day': day_name_it,  # Nome del giorno tradotto in italiano
                    'date': date.strftime('%d/%m'),
                    'temp_max': f"{item['main']['temp_max']:.1f}°C",
                    'temp_min': f"{item['main']['temp_min']:.1f}°C",
                    'condition': item['weather'][0]['description'].capitalize(),
                    'icon': item['weather'][0]['icon'],
                    'humidity': f"{item['main']['humidity']}%",
                    'wind': f"{item['wind']['speed']} m/s"
                })
        
        return {
            'current': current,
            'forecast': forecast
        }
    except Exception as e:
        # In caso di errore, utilizziamo dati simulati
        return get_mock_weather_data()

# Funzione per ottenere dati meteo simulati per Torre Annunziata
def get_mock_weather_data():
    # Dati meteo per Torre Annunziata (aggiornati manualmente)
    current_date = datetime.now()
    
    return {
        'current': {
            'temp': '22°C',
            'condition': 'Sereno',
            'humidity': '65%',
            'wind': '10 km/h',
            'pressure': '1015 hPa',
            'feels_like': '21°C',
            'visibility': '10 km',
            'clouds': '5%',
            'sunrise': '06:15',
            'sunset': '19:45',
            'icon': '01d'  # Codice icona per cielo sereno
        },
        'forecast': [
            {
                'day': 'Oggi',
                'date': current_date.strftime('%d/%m'),
                'temp_max': '24°C',
                'temp_min': '17°C',
                'condition': 'Sereno',
                'humidity': '65%',
                'wind': '10 km/h',
                'icon': '01d'
            },
            {
                'day': 'Domani',
                'date': (current_date + timedelta(days=1)).strftime('%d/%m'),
                'temp_max': '25°C',
                'temp_min': '18°C',
                'condition': 'Soleggiato',
                'humidity': '60%',
                'wind': '12 km/h',
                'icon': '01d'
            },
            {
                'day': traduci_giorno((current_date + timedelta(days=2)).strftime('%A')),
                'date': (current_date + timedelta(days=2)).strftime('%d/%m'),
                'temp_max': '23°C',
                'temp_min': '17°C',
                'condition': 'Parzialmente nuvoloso',
                'humidity': '68%',
                'wind': '15 km/h',
                'icon': '02d'
            },
            {
                'day': traduci_giorno((current_date + timedelta(days=3)).strftime('%A')),
                'date': (current_date + timedelta(days=3)).strftime('%d/%m'),
                'temp_max': '22°C',
                'temp_min': '16°C',
                'condition': 'Nuvoloso',
                'humidity': '70%',
                'wind': '18 km/h',
                'icon': '03d'
            },
            {
                'day': traduci_giorno((current_date + timedelta(days=4)).strftime('%A')),
                'date': (current_date + timedelta(days=4)).strftime('%d/%m'),
                'temp_max': '21°C',
                'temp_min': '15°C',
                'condition': 'Pioggia leggera',
                'humidity': '75%',
                'wind': '20 km/h',
                'icon': '10d'
            }
        ]
    }

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
        
        # Container con stile per il meteo attuale
        st.markdown("""
        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #0070c0;">Meteo Attuale - Torre Annunziata</h3>
        """, unsafe_allow_html=True)
        
        # Weather summary layout
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Determina se usare l'icona di OpenWeather o un'emoji
            if 'icon' in current:
                # Usa l'icona di OpenWeather se disponibile
                icon_url = f"http://openweathermap.org/img/wn/{current['icon']}@2x.png"
                st.markdown(f"""
                <div style="text-align: center;">
                    <img src="{icon_url}" width="100">
                    <h2 style="margin: 0;">{current['temp']}</h2>
                    <p>{current['condition']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Altrimenti, usa un'emoji
                condition = current['condition'].lower()
                weather_emoji = "☀️"  # Default - sole
                
                if "sereno" in condition or "soleggiato" in condition:
                    weather_emoji = "☀️"
                elif "nuvol" in condition:
                    if "parzialmente" in condition:
                        weather_emoji = "🌤️"
                    else:
                        weather_emoji = "☁️"
                elif "pioggia" in condition:
                    if "leggera" in condition:
                        weather_emoji = "🌦️"
                    else:
                        weather_emoji = "🌧️"
                elif "temporale" in condition:
                    weather_emoji = "⛈️"
                elif "neve" in condition:
                    weather_emoji = "❄️"
                elif "nebbia" in condition:
                    weather_emoji = "🌫️"
                    
                st.markdown(f"""
                <div style="text-align: center;">
                    <span style="font-size: 3rem;">{weather_emoji}</span>
                    <h2 style="margin: 0;">{current['temp']}</h2>
                    <p>{current['condition']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("<h4>Dettagli</h4>", unsafe_allow_html=True)
            st.markdown(f"**{get_text('feels_like')}**: {current['feels_like']}")
            st.markdown(f"**{get_text('humidity')}**: {current['humidity']}")
            st.markdown(f"**{get_text('pressure')}**: {current.get('pressure', 'N/A')}")
        
        with col3:
            st.markdown("<h4>Vento e Nuvole</h4>", unsafe_allow_html=True)
            st.markdown(f"**{get_text('wind')}**: {current['wind']}")
            st.markdown(f"**{get_text('clouds')}**: {current.get('clouds', 'N/A')}")
        
        with col4:
            st.markdown("<h4>Sole</h4>", unsafe_allow_html=True)
            if 'sunrise' in current and 'sunset' in current:
                st.markdown(f"**{get_text('sunrise')}**: {current['sunrise']}")
                st.markdown(f"**{get_text('sunset')}**: {current['sunset']}")
            else:
                st.markdown(f"**Aggiornamento**: {datetime.now().strftime('%H:%M')}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Previsioni future
        if st.session_state.weather_data['forecast']:
            st.subheader("Previsioni per i prossimi giorni")
            
            forecast_data = st.session_state.weather_data['forecast']
            cols = st.columns(len(forecast_data))
            
            for i, day_forecast in enumerate(forecast_data):
                with cols[i]:
                    # Determina se usare l'icona di OpenWeather o un'emoji
                    if 'icon' in day_forecast:
                        # Card stile per ogni previsione con icona OpenWeather
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                            <h4 style="margin-top: 0;">{day_forecast['day']}</h4>
                            <p style="color: #6c757d; margin: 0;">{day_forecast['date']}</p>
                            <img src="http://openweathermap.org/img/wn/{day_forecast['icon']}@2x.png" width="60">
                            <p>{day_forecast['condition']}</p>
                            <p style="font-weight: bold;">{get_text('temp_max')}: {day_forecast['temp_max']}<br>
                            {get_text('temp_min')}: {day_forecast['temp_min']}</p>
                            <p>{get_text('humidity')}: {day_forecast['humidity']}<br>
                            {get_text('wind')}: {day_forecast['wind']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Determina emoji in base alla condizione
                        condition = day_forecast['condition'].lower()
                        weather_emoji = "☀️"  # Default - sole
                        
                        if "sereno" in condition or "soleggiato" in condition:
                            weather_emoji = "☀️"
                        elif "nuvol" in condition:
                            if "parzialmente" in condition:
                                weather_emoji = "🌤️"
                            else:
                                weather_emoji = "☁️"
                        elif "pioggia" in condition:
                            if "leggera" in condition:
                                weather_emoji = "🌦️"
                            else:
                                weather_emoji = "🌧️"
                        elif "temporale" in condition:
                            weather_emoji = "⛈️"
                        elif "neve" in condition:
                            weather_emoji = "❄️"
                        elif "nebbia" in condition:
                            weather_emoji = "🌫️"
                        
                        # Card stile per ogni previsione con emoji
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                            <h4 style="margin-top: 0;">{day_forecast['day']}</h4>
                            <p style="color: #6c757d; margin: 0;">{day_forecast['date']}</p>
                            <span style="font-size: 2rem;">{weather_emoji}</span>
                            <p>{day_forecast['condition']}</p>
                            <p style="font-weight: bold;">{get_text('temp_max')}: {day_forecast['temp_max']}<br>
                            {get_text('temp_min')}: {day_forecast['temp_min']}</p>
                            <p>{get_text('humidity')}: {day_forecast['humidity']}<br>
                            {get_text('wind')}: {day_forecast['wind']}</p>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("Dati meteo non disponibili al momento.")
    
    # Attribuzione dati meteo
    st.caption("Dati meteo forniti da OpenWeather")
        
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