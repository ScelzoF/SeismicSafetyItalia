
import streamlit as st
from supabase_utils import inserisci_post, carica_post, inserisci_segnalazione, carica_segnalazioni

# Filtro AI semplice per contenuti inappropriati
PAROLE_VIETATE = ["parolaccia", "insulto", "spam", "offesa", "bestemmia"]

def è_contenuto_accettabile(testo):
    if not testo or len(testo.strip()) < 3:
        return False
    testo_lower = testo.lower()
    for parola in PAROLE_VIETATE:
        if parola in testo_lower:
            return False
    return True

def main():
    st.title("🗣️ Forum della Comunità")

    tab1, tab2, tab3 = st.tabs(["📢 Forum", "🚨 Segnalazioni", "🔗 Riferimenti"])

    with tab1:
        with st.form("nuovo_post"):
            username = st.text_input("👤 Il tuo nome")
            contenuto = st.text_area("💬 Scrivi qualcosa")
            invia = st.form_submit_button("✉️ Invia")

            if invia:
                if not è_contenuto_accettabile(contenuto):
                    st.error("❌ Contenuto non valido o inappropriato.")
                else:
                    successo, messaggio = inserisci_post(username, contenuto)
                    st.success(messaggio) if successo else st.error(messaggio)

        st.divider()
        st.subheader("📚 Post recenti (raggruppati)")

        posts = carica_post()
        posts_validi = [p for p in posts if è_contenuto_accettabile(p.get("contenuto", ""))]

        if posts_validi:
            blocco = ""
            for post in reversed(posts_validi):
                blocco += f"👤 <strong>{post['username']}</strong> <small>({post.get('data', '')[:16]})</small><br>{post['contenuto']}<br><br>"
            st.markdown(f"<div style='padding: 15px; border: 1px solid #ccc; border-radius: 8px; background-color: #eef1f5;'>{blocco}</div>", unsafe_allow_html=True)
        else:
            st.info("Nessun post valido disponibile.")

    with tab2:
       # Function to display the report form
def show_report_form():
    st.subheader("Segnalazioni e Testimonianze")
    
    st.write("""
    Utilizza questo modulo per segnalare fenomeni sismici o vulcanici osservati nella tua zona.
    Le segnalazioni aiutano la comunità scientifica e gli altri utenti a monitorare meglio l'attività.
    """)
    
    # Report form
    with st.form("report_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("Località:")
            event_time = st.time_input("Ora dell'evento:")
            event_date = st.date_input("Data dell'evento:")
        
        with col2:
            event_type = st.selectbox(
                "Tipo di evento:",
                ["Terremoto", "Boato", "Fumarola", "Sollevamento del suolo", "Subsidenza", "Altro"]
            )
            
            intensity = st.slider(
                "Intensità percepita (1-10):",
                min_value=1,
                max_value=10,
                value=5
            )
        
        description = st.text_area("Descrizione dell'evento:")
        
        submit_report = st.form_submit_button("Invia segnalazione")
        
        if submit_report:
            if location and description:
                st.success("Grazie per la tua segnalazione! È stata inviata al nostro team.")
                
                # In a real application, this would be saved to a database
                # For this prototype, we'll just display a confirmation
                st.write("Dettagli della segnalazione:")
                
                event_datetime = datetime.combine(event_date, event_time)
                
                report_details = {
                    "Località": location,
                    "Data e ora": event_datetime.strftime("%d/%m/%Y %H:%M"),
                    "Tipo di evento": event_type,
                    "Intensità percepita": f"{intensity}/10",
                    "Descrizione": description
                }
                
                for key, value in report_details.items():
                    st.write(f"**{key}:** {value}")
            else:
                st.error("Per favore compila tutti i campi richiesti.")

            if invia:
                if not è_contenuto_accettabile(contenuto):
                    st.error("❌ Segnalazione rifiutata: contenuto non valido.")
                else:
                    successo, messaggio = inserisci_segnalazione(username, contenuto)
                    st.success(messaggio) if successo else st.error(messaggio)

        st.divider()
        st.subheader("📒 Storico segnalazioni")

        segnalazioni = carica_segnalazioni()
        segnalazioni_valide = [s for s in segnalazioni if è_contenuto_accettabile(s.get("contenuto", ""))]

        if segnalazioni_valide:
            blocco = ""
            for s in reversed(segnalazioni_valide):
                blocco += f"👤 <strong>{s['username']}</strong> <small>({s.get('data', '')[:16]})</small><br>{s['contenuto']}<br><br>"
            st.markdown(f"<div style='padding: 15px; border: 1px solid #ccc; border-radius: 8px; background-color: #fdf2e9;'>{blocco}</div>", unsafe_allow_html=True)
        else:
            st.info("Nessuna segnalazione disponibile.")

    with tab3:
        st.subheader("📎 Riferimenti utili")
        st.markdown("""
        - [Protezione Civile](https://www.protezionecivile.gov.it/)
        - [INGV - Istituto Nazionale di Geofisica e Vulcanologia](https://www.ingv.it/)
        - [Copernicus Emergency Management Service](https://emergency.copernicus.eu/)
        """)
