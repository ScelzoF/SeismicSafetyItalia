
import streamlit as st
from datetime import datetime
import base64
import os

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
- **Chat pubblica**: Sistema attivo per scambio diretto tra utenti (tramite Supabase)
- **Segnalazioni**: Possibilità di inviare eventi o osservazioni direttamente nella piattaforma

### Fonti dei dati

I dati utilizzati in questa applicazione provengono da fonti ufficiali:

- **INGV** (Istituto Nazionale di Geofisica e Vulcanologia)
- **USGS** (United States Geological Survey)
- **Protezione Civile Italiana)

### Affidabilità dei Dati e Simulazioni

- [OK] I dati sismici sono reali, aggiornati automaticamente ogni 15 minuti, provenienti da API ufficiali INGV e USGS.
- [OK] Le visualizzazioni (grafici, mappe) sono basate esclusivamente su dati autentici.
- [OK] Il database community (SQLite) e la chat pubblica sono reali e funzionanti.
- [Warning] La sezione **Previsioni** utilizza algoritmi statistici (machine learning) che **non hanno valore scientifico certificato**. Le previsioni sono da considerarsi **ipotesi probabilistiche non ufficiali**.
- [Alert] L'accuratezza dichiarata nei modelli previsionali è una **stima interna** e **non deve essere interpretata come garanzia di affidabilità**.

### Disclaimer
Questa applicazione è uno strumento informativo che **non sostituisce i canali ufficiali di allerta**. Per aggiornamenti e indicazioni operative, fare sempre riferimento alla Protezione Civile e agli enti governativi competenti.

---
**Progetto ideato e sviluppato da Fabio Scelzo**  
📧 meteotorre@gmail.com
""")

import streamlit as st
import base64

def render_svg(svg_file):
    try:
        with open(svg_file, 'rb') as f:
            svg_data = f.read()
            b64_svg = base64.b64encode(svg_data).decode()
            st.markdown(f'<img src="data:image/svg+xml;base64,{b64_svg}" width="100%" />', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Impossibile caricare l'immagine {os.path.basename(svg_file)}")
