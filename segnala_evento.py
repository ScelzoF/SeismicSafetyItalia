
import streamlit as st
from supabase_utils import invia_segnalazione

st.title("Invia una segnalazione")

with st.form("form_segnalazione"):
    localita = st.text_input("Località", "")  # Campo di testo per la località
    tipo_evento = st.selectbox("Tipo di evento", ["Terremoto", "Frana", "Altro"])  # Seleziona tipo di evento
    intensita = st.slider("Intensità percepita", 1, 10, 5)  # Slider per intensità
    descrizione = st.text_area("Descrizione")  # Campo di testo per la descrizione
    invia = st.form_submit_button("Invia segnalazione")

    if invia:
        # Invio la segnalazione
        successo, messaggio = invia_segnalazione(localita, tipo_evento, intensita, descrizione)
        if successo:
            st.success("✅ " + messaggio)
        else:
            st.error("❌ " + messaggio)
