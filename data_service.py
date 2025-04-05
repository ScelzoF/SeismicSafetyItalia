
import pandas as pd
import streamlit as st
from datetime import datetime
from monitoraggio_fallback import dati_sismici

# Main function to fetch earthquake data using fallback system
def fetch_earthquake_data():
    try:
        data, fonte_messaggio = dati_sismici()

        if data is None or data.empty:
            st.error("Nessun dato disponibile.")
            return pd.DataFrame(), fonte_messaggio

        # Convert time to datetime and format it
        data['datetime'] = pd.to_datetime(data['time'], errors='coerce')
        data = data.dropna(subset=['datetime'])
        data = data.sort_values(by='datetime', ascending=False)
        data['formatted_time'] = data['datetime'].dt.strftime('%d/%m/%Y %H:%M:%S')

        return data, fonte_messaggio

    except Exception as e:
        st.error(f"Errore durante il recupero dei dati sismici: {str(e)}")
        return pd.DataFrame(), "Errore"
