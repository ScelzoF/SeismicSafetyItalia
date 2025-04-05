
import pandas as pd
import streamlit as st
from monitoraggio_fallback import dati_sismici

def get_sismic_data(show_debug=False):
    try:
        df, fonte = dati_sismici(show_debug=show_debug)

        if df is None or df.empty:
            return pd.DataFrame(), fonte

        df['datetime'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['datetime'])
        df = df.sort_values(by='datetime', ascending=False)
        df['formatted_time'] = df['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')

        return df, fonte
    except Exception as e:
        errore = f"⚠️ Errore durante il recupero dei dati: {e}"
        if show_debug:
            st.error(errore)
        return pd.DataFrame(), errore
