import streamlit as st

from fallback_sismico import get_sismic_data

def process_data():
    st.subheader("Dati sismici in tempo reale")
    show_debug = st.sidebar.checkbox("Mostra dettagli tecnici")

    with st.spinner("🔄 Recupero dati sismici..."):
        df, fonte = get_sismic_data()

    if show_debug:
        st.success("✅ DEBUG: process_data è stata eseguita!")

    if not df.empty:
        st.info(fonte)
        st.dataframe(df, width="stretch")
    else:
        st.warning(fonte)
