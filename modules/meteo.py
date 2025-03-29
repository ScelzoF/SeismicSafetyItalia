def show():
    import streamlit as st
    import requests
    from streamlit_js_eval import streamlit_js_eval

    st.title("🌤️ Meteo Attuale")

    API_KEY = st.secrets.get("OPENWEATHER_API_KEY")
    if not API_KEY:
        st.error("🔑 Chiave API OpenWeather mancante nei secrets.")
        return

    metodo = st.radio("🔍 Metodo:", ["📍 Usa posizione attuale", "🏙️ Inserisci città"])

    if metodo == "📍 Usa posizione attuale":
        coords = streamlit_js_eval(js_expressions='navigator.geolocation.getCurrentPosition((pos) => ({lat: pos.coords.latitude, lon: pos.coords.longitude}))', key="geo")
        if coords and "lat" in coords and "lon" in coords:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={API_KEY}&units=metric&lang=it"
        else:
            st.warning("Geolocalizzazione non disponibile.")
            return
    else:
        città = st.text_input("Inserisci città", value="Napoli")
        if not città:
            return
        url = f"https://api.openweathermap.org/data/2.5/weather?q={città}&appid={API_KEY}&units=metric&lang=it"

    try:
        res = requests.get(url)
        data = res.json()
        if res.status_code != 200 or "main" not in data:
            st.error("❌ Località non trovata o errore nella richiesta.")
            return

        st.subheader(f"☁️ Meteo a {data['name']}")
        st.metric("🌡️ Temperatura", f"{data['main']['temp']} °C")
        st.metric("💧 Umidità", f"{data['main']['humidity']}%")
        st.metric("🌬️ Vento", f"{data['wind']['speed']} m/s")
        st.info(f"📌 Descrizione: {data['weather'][0]['description'].capitalize()}")

    except Exception as e:
        st.error(f"Errore nel recupero meteo: {e}")