
import pandas as pd
import streamlit as st
from monitoraggio_fallback import dati_sismici

def get_sismic_data():
    try:
        df, fonte = dati_sismici()

        if df is None or df.empty:
            return pd.DataFrame(), "⚠️ Nessun dato disponibile."

        df['datetime'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['datetime'])
        df = df.sort_values(by='datetime', ascending=False)
        df['formatted_time'] = df['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')

        return df, fonte
    except Exception as e:
        st.error(f"Errore fallback: {e}")
        return pd.DataFrame(), "⚠️ Errore nel recupero dei dati."
