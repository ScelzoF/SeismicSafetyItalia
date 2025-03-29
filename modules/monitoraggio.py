
import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import plotly.express as px
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

def show():
    st.header("📡 Monitoraggio Sismico e Meteo Avanzato")

    # Geolocalizzazione
    coords = streamlit_js_eval(
        js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))',
        key="get_geolocation"
    )

    # Meteo
    api_key = st.secrets.get("OPENWEATHER_API_KEY", "")
    city = st.text_input("📍 Inserisci una città per visualizzare il meteo", value="Napoli")
    if api_key and city:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
        response = requests.get(weather_url)
        if response.status_code == 200:
            data = response.json()
            st.subheader(f"☀️ Meteo a {city}")
            st.markdown(f"**Temperatura:** {data['main']['temp']}°C")
            st.markdown(f"**Condizioni:** {data['weather'][0]['description'].capitalize()}")
        else:
            st.warning("⚠️ Meteo non disponibile.")
    else:
        st.info("ℹ️ Inserisci una città o verifica l’API Key OpenWeather.")

    # Eventi sismici INGV
    st.subheader("🇮🇹 Eventi sismici in Italia (INGV)")
    ingv_url = f"https://webservices.ingv.it/fdsnws/event/1/query?format=geojson&starttime={datetime.utcnow().date()}T00:00:00"
    try:
        resp = requests.get(ingv_url)
        quakes = resp.json()["features"]
        rows = []
        for q in quakes:
            prop = q["properties"]
            mag = prop.get("mag", 0)
            place = prop.get("place", "Sconosciuto")
            time_str = prop.get("time", "")
            try:
                time = pd.to_datetime(time_str)
            except:
                time = None
            rows.append({"Luogo": place, "Magnitudo": mag, "Data/Ora UTC": time})
        df_ita = pd.DataFrame(rows)
        st.dataframe(df_ita, use_container_width=True)

        # Grafico media magnitudo giornaliera
        if not df_ita.empty:
            df_ita = df_ita.dropna(subset=["Data/Ora UTC"])
            media_mag = df_ita.groupby(df_ita["Data/Ora UTC"].dt.date)["Magnitudo"].mean().reset_index()
            fig = px.line(media_mag, x="Data/Ora UTC", y="Magnitudo", title="📈 Media Magnitudo Giornaliera (Italia)")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Errore dati INGV: {e}")

    # Eventi sismici globali (USGS)
    st.subheader("🌎 Eventi globali (USGS)")
    usgs_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    try:
        r = requests.get(usgs_url)
        data = r.json()
        quakes = []
        for f in data["features"]:
            prop = f["properties"]
            coords_q = f["geometry"]["coordinates"]
            quakes.append({
                "Luogo": prop.get("place", "N/A"),
                "Magnitudo": prop.get("mag", 0),
                "Data/Ora UTC": datetime.utcfromtimestamp(prop["time"] / 1000),
                "lat": coords_q[1],
                "lon": coords_q[0],
            })
        df_global = pd.DataFrame(quakes)
        st.dataframe(df_global[["Luogo", "Magnitudo", "Data/Ora UTC"]], use_container_width=True)

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(latitude=42.5, longitude=12.5, zoom=3),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df_global,
                    get_position='[lon, lat]',
                    get_color='[255, 0, 0, 160]',
                    get_radius=50000,
                )
            ]
        ))
    except Exception as e:
        st.warning(f"Errore dati USGS: {e}")

    # Mappa centrata sull'Italia se geolocalizzazione disponibile
    if coords and "lat" in coords and "lon" in coords:
        st.map(pd.DataFrame([coords]), zoom=5)
