import streamlit as st

from fallback_sismico import get_sismic_data

def process_data():
    st.subheader("Dati sismici in tempo reale")
    df, fonte = get_sismic_data()
    if not df.empty:
        st.info(fonte)
        st.dataframe(df)
    else:
        st.warning(fonte)
