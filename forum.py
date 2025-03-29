
import streamlit as st
from supabase_utils import invia_segnalazione

st.title("🗣️ Forum della Comunità")

tab1, tab2, tab3 = st.tabs(["📢 Forum", "🚨 Segnalazioni", "🔗 Riferimenti"])

with tab2:
    st.subheader("Segnalazioni e Testimonianze")
    
    # Segnalazione form layout
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

# Keep the rest of the content of forum.py unchanged
