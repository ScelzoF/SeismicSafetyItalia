
import streamlit as st
from supabase_utils import invia_segnalazione

st.title("Invia una segnalazione")

with st.form("form_segnalazione"):
    localita = st.text_input("Località", "Torre Annunziata")
    tipo_evento = st.selectbox("Tipo di evento", ["Terremoto", "Frana", "Altro"])
    intensita = st.slider("Intensità percepita", 1, 10, 5)
    descrizione = st.text_area("Descrizione")
    invia = st.form_submit_button("Invia segnalazione")

    if invia:
        successo, messaggio = invia_segnalazione(localita, tipo_evento, intensita, descrizione)
        if successo:
            st.success("✅ " + messaggio)
        else:
            st.error("❌ " + messaggio)
