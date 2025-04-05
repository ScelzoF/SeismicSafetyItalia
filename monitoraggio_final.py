import streamlit as st

from fallback_sismico import get_sismic_data

def process_data():
    st.subheader("Dati sismici in tempo reale")
    debug = st.sidebar.checkbox("Mostra dettagli tecnici")

    with st.spinner("🔄 Recupero dati sismici..."):
        df, fonte = get_sismic_data()

    if debug:
        st.success("✅ DEBUG: process_data è stata eseguita!")

    if not df.empty:
        st.info(fonte)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning(fonte)
