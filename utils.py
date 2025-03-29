import streamlit as st
from datetime import datetime
import base64

# Function to toggle notification state
def toggle_notifications():
    st.session_state.notification_enabled = not st.session_state.notification_enabled
    
    if st.session_state.notification_enabled:
        st.toast("🔔 Notifiche abilitate")
    else:
        st.toast("🔕 Notifiche disabilitate")

# Function to display the about page
def show_about_page(get_text):
    st.header("ℹ️ " + get_text('about'))
    
    st.markdown("""
    ## Monitoraggio Sismico - Campania
    
    Questa applicazione è stata sviluppata per fornire alla comunità uno strumento per il monitoraggio dell'attività sismica e vulcanica nella regione Campania, con particolare attenzione alle aree del Vesuvio e dei Campi Flegrei (Solfatara, Pozzuoli).
    
    ### Funzionalità
    
    - **Monitoraggio in tempo reale**: Dati sismici aggiornati da INGV e USGS
    - **Visualizzazioni interattive**: Mappe e grafici per comprendere al meglio l'attività sismica
    - **Informazioni di emergenza**: Guide di evacuazione e comportamento in caso di evento sismico
    - **Community**: Forum per la condivisione di informazioni ed esperienze
    
    ### Fonti dei dati
    
    I dati utilizzati in questa applicazione provengono da fonti ufficiali:
    
    - **INGV** (Istituto Nazionale di Geofisica e Vulcanologia)
    - **USGS** (United States Geological Survey)
    - **Protezione Civile Italiana**
    
    ### Disclaimer
    
    Questa applicazione è uno strumento informativo e non sostituisce i canali ufficiali di comunicazione in caso di emergenza. In caso di evento sismico o vulcanico, seguire sempre le indicazioni delle autorità competenti.
    
    ### Contatti
    
    Per , feedback o richieste di supporto, è possibile contattare lo sviluppatore, nella persona di Fabio SCELZO, all'indirizzo email: meteotorre@gmail.com
    """)
    
    # Show info about data refresh
    st.info("""
    I dati sismici vengono aggiornati automaticamente ogni 5 minuti. 
    È comunque possibile forzare un aggiornamento tramite il pulsante "Aggiorna dati" presente nella barra laterale.
    """)
    
    # Technical information expander
    with st.expander("Informazioni tecniche"):
        st.markdown("""
        ### Tecnologie utilizzate
        
        - **Backend**: Python, Streamlit
        - **Dati**: API INGV e USGS
        - **Visualizzazioni**: Plotly, Folium
        
        ### Limitazioni attuali
        
        - I dati mostrati hanno un ritardo variabile rispetto al tempo reale, dipendente dalle API esterne
        - Le previsioni sono basate esclusivamente su trend storici e non garantiscono accuratezza predittiva
        - Il sistema di notifiche funziona solo mentre l'applicazione è aperta nel browser
        
        ### Sviluppi futuri
        
        - Integrazione con sistemi di allerta nazionali
        - Analisi avanzata dei pattern sismici
        - App mobile dedicata con notifiche push
        - Supporto multilingua esteso
        """)

    # Version and last update info
    st.caption(f"Version .0.0 | Last updated: {datetime.now().strftime('%d/%m/%Y')}")

# Function to render SVG from file
def render_svg(svg_file):
    with open(svg_file, "r") as f:
        svg = f.read()
        
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = f'''
        <img src="data:image/svg+xml;base64,{b64}" style="max-width: 00%; height: auto;">
    '''
    return html
