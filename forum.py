
import streamlit as st
from supabase_utils import inserisci_post, carica_post, inserisci_segnalazione, carica_segnalazioni
from datetime import datetime

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

def show_report_form():
    st.subheader("Segnalazioni e Testimonianze")
    
    st.write(
        "Utilizza questo modulo per segnalare fenomeni sismici o vulcanici osservati nella tua zona. "
        "Le segnalazioni aiutano la comunità scientifica e gli altri utenti a monitorare meglio l'attività."
    )
    
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
                # Call the inserisci_segnalazione function to insert the data into Supabase
                successo, messaggio = inserisci_segnalazione(location, event_type, event_time, event_date, intensity, description)
                if successo:
                    st.success(messaggio)
                else:
                    st.error(messaggio)
                
                # Display the confirmation and report details
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

def main():
    # Display the report form and other functionalities
    show_report_form()

if __name__ == "__main__":
    main()
