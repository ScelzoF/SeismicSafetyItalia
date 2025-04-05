
import streamlit as st
from fallback_wrapper import get_sismic_data

def process_data():
    show_debug = st.sidebar.checkbox('Mostra dettagli tecnici')
    with st.spinner('🔄 Recupero dati sismici...'):
        df, fonte = get_sismic_data(show_debug=show_debug)

    if not df.empty:
        if show_debug:
            st.success("✅ DEBUG: process_data è stata eseguita!")
        st.info(fonte)
        st.dataframe(df)
    else:
        st.warning("⚠️ Nessun dato disponibile al momento.")
