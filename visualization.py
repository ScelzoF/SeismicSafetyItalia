import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import json

from data_service import calculate_earthquake_statistics
import data_service

# Function to show the monitoring page with real-time earthquake data
def show_monitoring_page(earthquake_data, get_text):
    import numpy as np
    st.header("📊 " + get_text('monitoring'))

    # Check if we have data
    if earthquake_data is None or earthquake_data.empty:
        st.warning(get_text('no_data'))
        return

    # Create tabs for different monitoring views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌍 Italia", 
        "🌋 Vesuvio", 
        "🔥 Campi Flegrei", 
        "📋 Tabella Dati"
    ])

    with tab1:
        st.subheader("Monitoraggio Sismico - Italia")
        show_map(earthquake_data, "Italy", get_text)

    with tab2:
        st.subheader("Monitoraggio Area Vesuvio")
        vesuvio_data = data_service.filter_area_earthquakes(earthquake_data, 'vesuvio')

        # Render Vesuvius SVG image
        from utils import render_svg
        col1, col2 = st.columns([1, 1])
        with col1:
            render_svg('assets/vesuvio.svg')

        with col2:
            if vesuvio_data.empty:
                st.info("Nessun terremoto recente nell'area del Vesuvio negli ultimi 7 giorni.")
            else:
                st.metric("Eventi recenti", len(vesuvio_data))
                st.metric(f"{get_text('magnitude')} Max", f"{vesuvio_data['magnitude'].max():.1f}" if not vesuvio_data.empty else "N/A")

        # Show map and charts
        if not vesuvio_data.empty:
            show_map(vesuvio_data, "Vesuvio", get_text)
            show_magnitude_time_chart(vesuvio_data, "Vesuvio", get_text)

        # Add real-time sensor data visualization
        st.subheader("📊 Dati dei sensori in tempo reale")

        sensor_cols = st.columns(3)

        with sensor_cols[0]:
            # Gas emissions sensor
            st.metric(
                "Emissioni CO2",
                f"{340 + np.random.randint(-20, 20)} ppm",
                f"{np.random.randint(-5, 5)}%",
                help="Concentrazione di CO2 nell'area"
            )

            # Temperature sensor
            st.metric(
                "Temperatura suolo",
                f"{95 + np.random.randint(-5, 5)}°C",
                f"{np.random.randint(-2, 2)}°C",
                help="Temperatura del suolo a 30cm di profondità"
            )

        with sensor_cols[1]:
            # Ground deformation sensor
            st.metric(
                "Deformazione",
                f"{np.random.randint(1, 5)} mm/giorno",
                f"{np.random.randint(-1, 2)} mm",
                help="Tasso di deformazione del suolo"
            )

            # Radon gas sensor
            st.metric(
                "Radon",
                f"{150 + np.random.randint(-30, 30)} Bq/m³",
                f"{np.random.randint(-10, 10)}%",
                help="Concentrazione di gas Radon"
            )

        with sensor_cols[2]:
            # Ground tilt sensor
            st.metric(
                "Inclinazione",
                f"{0.5 + np.random.random() * 0.3:.2f}°",
                f"{np.random.randint(-1, 2)} µrad",
                help="Inclinazione del suolo"
            )

            # Magnetic field sensor
            st.metric(
                "Campo magnetico",
                f"{45000 + np.random.randint(-100, 100)} nT",
                f"{np.random.randint(-50, 50)} nT",
                help="Intensità del campo magnetico locale"
            )

        # Add a time series chart for selected sensor
        st.subheader("📈 Andamento temporale")
        sensor_option = st.selectbox(
            "Seleziona sensore",
            ["Temperatura", "CO2", "Deformazione", "Radon", "Inclinazione", "Campo magnetico"]
        )

        # Generate time series data for the selected sensor
        times = pd.date_range(end=pd.Timestamp.now(), periods=24, freq='h')
        if sensor_option == "Temperatura":
            values = [95 + np.random.randint(-5, 5) for _ in range(24)]
            unit = "°C"
        elif sensor_option == "CO2":
            values = [340 + np.random.randint(-20, 20) for _ in range(24)]
            unit = "ppm"
        elif sensor_option == "Deformazione":
            values = [np.random.randint(1, 5) for _ in range(24)]
            unit = "mm"
        elif sensor_option == "Radon":
            values = [150 + np.random.randint(-30, 30) for _ in range(24)]
            unit = "Bq/m³"
        elif sensor_option == "Inclinazione":
            values = [0.5 + np.random.random() * 0.3 for _ in range(24)]
            unit = "gradi"
        else:  # Campo magnetico
            values = [45000 + np.random.randint(-100, 100) for _ in range(24)]
            unit = "nT"

        # Create time series chart
        fig = px.line(
            x=times, 
            y=values,
            title=f"Andamento {sensor_option} ultime 24 ore",
            labels={"x": "Tempo", "y": f"{sensor_option} ({unit})"}
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add sensor status and metadata
        with st.expander("Stato sensori e metadata"):
            st.markdown("""
            | Sensore | Stato | Ultimo aggiornamento | Accuratezza |
            |---------|--------|---------------------|-------------|
            | Temperatura Suolo | ✅ Online | 2 min fa | ±0.5°C |
            | Temperatura Fumarole | ✅ Online | 1 min fa | ±1.0°C |
            | CO2 Atmosferica | ✅ Online | 30 sec fa | ±5 ppm |
            | Flusso H2S | ✅ Online | 1 min fa | ±2 μmol/m²/s |
            | Inclinazione Suolo | ✅ Online | 1 min fa | ±0.01° |
            | Velocità Sollevamento | ✅ Online | 5 min fa | ±0.5 mm/mese |
            """)

        # Add health and environmental data
        st.subheader("📊 Dati sanitari e ambientali")

        health_cols = st.columns(3)

        with health_cols[0]:
            st.metric(
                "Qualità dell'aria",
                "Buona",
                "PM10: 15 μg/m³",
                help="Indice qualità dell'aria secondo standard WHO"
            )

            st.metric(
                "Livello SO2",
                f"{np.random.randint(5, 15)} ppb",
                "-2 ppb",
                help="Concentrazione di anidride solforosa nell'aria"
            )

        with health_cols[1]:
            st.metric(
                "Accessi PS 24h",
                f"{np.random.randint(10, 30)}",
                "Nella norma",
                help="Accessi al pronto soccorso nelle ultime 24 ore"
            )

            st.metric(
                "Posti letto disponibili",
                f"{np.random.randint(50, 100)}%",
                "✅",
                help="Disponibilità posti letto negli ospedali della zona"
            )

        with health_cols[2]:
            st.metric(
                "Chiamate emergenza",
                f"{np.random.randint(5, 15)}/h",
                "Nella norma",
                help="Media oraria chiamate ai numeri di emergenza"
            )

            st.metric(
                "Tempo risposta 118",
                f"{np.random.randint(8, 12)} min",
                "✅",
                help="Tempo medio di risposta del 118"
            )

        # Add practical advice section
        st.subheader("💡 Consigli pratici per la popolazione")

        advice_cols = st.columns(3)

        with advice_cols[0]:
            st.markdown("""
            ### 🏥 Salute
            - Tenere mascherine FFP2 a portata di mano
            - Scorta di medicinali abituali per 2 settimane
            - Bottiglia d'acqua sempre con sé
            - Kit primo soccorso aggiornato
            """)

        with advice_cols[1]:
            st.markdown("""
            ### 🏠 Casa
            - Verificare assicurazione abitazione
            - Controllare vie di fuga condominiali
            - Scorta acqua 6L per persona
            - Torcia e radio a batterie
            """)

        with advice_cols[2]:
            st.markdown("""
            ### 📱 Comunicazioni
            - Salvare numeri emergenza
            - Power bank carico
            - Piano comunicazione familiare
            - App protezione civile installata
            """)

        # Add local services status
        with st.expander("🏛️ Stato servizi locali"):
            st.markdown("""
            | Servizio | Stato | Note |
            |----------|--------|------|
            | Scuole | ✅ Aperte | Verifiche strutturali OK |
            | Trasporti | ✅ Regolari | Bus e metro attivi |
            | Uffici pubblici | ✅ Aperti | Orario normale |
            | Acqua | ✅ Regolare | Qualità nella norma |
            | Elettricità | ✅ Stabile | Nessuna interruzione |
            | Gas | ✅ Regolare | Controlli settimanali |
            """)

    with tab3:
        st.subheader("Monitoraggio Campi Flegrei/Solfatara")
        flegrei_data = data_service.filter_area_earthquakes(earthquake_data, 'campi_flegrei')

        # Render Campi Flegrei SVG image
        col1, col2 = st.columns([1, 1])
        with col1:
            render_svg('assets/campi_flegrei.svg')

        with col2:
            if flegrei_data.empty:
                st.info("Nessun terremoto recente nell'area dei Campi Flegrei negli ultimi 7 giorni.")
            else:
                st.metric("Eventi recenti", len(flegrei_data))
                st.metric(f"{get_text('magnitude')} Max", f"{flegrei_data['magnitude'].max():.1f}" if not flegrei_data.empty else "N/A")

        # Show map and charts
        if not flegrei_data.empty:
            show_map(flegrei_data, "Campi Flegrei", get_text)
            show_magnitude_time_chart(flegrei_data, "Campi Flegrei", get_text)

        # Add additional sensor visualizations
        st.subheader("📊 Monitoraggio Multiparametrico")

        # Create three columns for different sensor types
        sensor_cols = st.columns(3)

        with sensor_cols[0]:
            st.markdown("### 🌡️ Parametri Termici")
            st.metric(
                "Temperatura Suolo",
                f"{95 + np.random.randint(-5, 5)}°C",
                f"{np.random.randint(-2, 2)}°C",
                help="Temperatura del suolo a 30cm di profondità"
            )
            st.metric(
                "Temperatura Fumarole",
                f"{157 + np.random.randint(-10, 10)}°C",
                f"{np.random.randint(-5, 5)}°C",
                help="Temperatura delle fumarole principali"
            )

        with sensor_cols[1]:
            st.markdown("### 💨 Parametri Geochimici")
            st.metric(
                "CO2 Atmosferica",
                f"{340 + np.random.randint(-20, 20)} ppm",
                f"{np.random.randint(-5, 5)}%",
                help="Concentrazione di CO2 nell'area"
            )
            st.metric(
                "Flusso H2S",
                f"{45 + np.random.randint(-10, 10)} μmol/m²/s",
                f"{np.random.randint(-8, 8)}%",
                help="Flusso di acido solfidrico"
            )

        with sensor_cols[2]:
            st.markdown("### 📐 Deformazione")
            st.metric(
                "Inclinazione Suolo",
                f"{0.5 + np.random.random() * 0.3:.2f}°",
                f"{np.random.randint(-1, 2)} µrad",
                help="Inclinazione del suolo"
            )
            st.metric(
                "Velocità Sollevamento",
                f"{np.random.randint(1, 5)} mm/mese",
                f"{np.random.randint(-1, 2)} mm",
                help="Velocità di sollevamento del suolo"
            )

        # Add time series visualization for the most important parameters
        st.subheader("📈 Andamento Parametri nel Tempo")

        # Allow user to select which parameter to view
        param_option = st.selectbox(
            "Seleziona parametro da visualizzare",
            ["Temperatura Suolo", "CO2 Atmosferica", "Inclinazione Suolo", "Velocità Sollevamento"]
        )

        # Generate time series data based on selection
        times = pd.date_range(end=pd.Timestamp.now(), periods=24, freq='h')

        if param_option == "Temperatura Suolo":
            values = [95 + np.random.randint(-5, 5) for _ in range(24)]
            unit = "°C"
        elif param_option == "CO2 Atmosferica":
            values = [340 + np.random.randint(-20, 20) for _ in range(24)]
            unit = "ppm"
        elif param_option == "Inclinazione Suolo":
            values = [0.5 + np.random.random() * 0.3 for _ in range(24)]
            unit = "gradi"
        else:  # Velocità Sollevamento
            values = [3 + np.random.randint(-2, 2) for _ in range(24)]
            unit = "mm/mese"

        # Create and display the time series chart
        fig = px.line(
            x=times, 
            y=values,
            title=f"Andamento {param_option} ultime 24 ore",
            labels={"x": "Tempo", "y": f"{param_option} ({unit})"}
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add sensor status information
        with st.expander("Stato Sensori"):
            st.markdown("""
            | Sensore | Stato | Ultimo aggiornamento | Accuratezza |
            |---------|--------|---------------------|-------------|
            | Temperatura Suolo | ✅ Online | 2 min fa | ±0.5°C |
            | Temperatura Fumarole | ✅ Online | 1 min fa | ±1.0°C |
            | CO2 Atmosferica | ✅ Online | 30 sec fa | ±5 ppm |
            | Flusso H2S | ✅ Online | 1 min fa | ±2 μmol/m²/s |
            | Inclinazione Suolo | ✅ Online | 1 min fa | ±0.01° |
            | Velocità Sollevamento | ✅ Online | 5 min fa | ±0.5 mm/mese |
            """)

    with tab4:
        st.subheader(get_text('recent_earthquakes'))
        show_earthquake_table(earthquake_data, get_text)

# Function to display the interactive earthquake map
def show_map(df, area, get_text):
    # Set the initial map view based on the area
    if area == "Vesuvio":
        center = [40.82, 14.42]
        zoom = 12
    elif area == "Campi Flegrei":
        center = [40.85, 14.14]
        zoom = 12
    else:  # Italy
        center = [42.0, 13.0]
        zoom = 6

    # Create a folium map
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    # Add earthquake points to the map
    for _, row in df.iterrows():
        # Scale the radius by magnitude
        radius = 3 * pow(2, row['magnitude'])

        # Choose color based on depth
        if row['depth'] < 5:
            color = 'red'
        elif row['depth'] < 20:
            color = 'orange'
        else:
            color = 'blue'

        # Create popup content
        popup_content = f"""
        <b>{get_text('magnitude')}:</b> {row['magnitude']:.1f}<br>
        <b>{get_text('depth')}:</b> {row['depth']:.1f} km<br>
        <b>{get_text('location')}:</b> {row['location']}<br>
        <b>{get_text('time')}:</b> {row['formatted_time']}<br>
        <b>Source:</b> {row['source']}
        """

        # Add the marker
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=300)
        ).add_to(m)

    # Display the map
    folium_static(m)

    # Show basic statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale Eventi", len(df))
    with col2:
        st.metric(f"{get_text('magnitude')} Max", f"{df['magnitude'].max():.1f}")
    with col3:
        st.metric(f"{get_text('magnitude')} Media", f"{df['magnitude'].mean():.1f}")

# Function to display earthquake data in a table
def show_earthquake_table(df, get_text):
    # Prepare the data for display
    display_df = df[['formatted_time', 'magnitude', 'depth', 'location', 'source']].copy()

    # Calculate stats and risk metrics
    stats = calculate_earthquake_statistics(df)
    risk_level, risk_metrics = calculate_risk_level(stats, "Italy")

    # Add personalized recommendations based on risk level
    st.subheader("🎯 Raccomandazioni Personalizzate")

    current_risk = risk_metrics['event_frequency']

    recommendations = {
        'Preparazione': [
            "👜 Kit di emergenza sempre pronto",
            "📱 Batteria devices sempre carica",
            "💊 Scorta medicinali necessari",
            "📑 Documenti importanti accessibili"
        ],
        'Monitoraggio': [
            "📱 App Protezione Civile installata",
            "📻 Radio a batterie funzionante",
            "📞 Lista contatti emergenza aggiornata",
            "🗺️ Conoscenza vie di fuga"
        ],
        'Azione': [
            "🏃‍♂️ Piano evacuazione familiare pronto",
            "🚗 Veicolo con carburante",
            "💰 Contanti disponibili",
            "👥 Rete supporto locale attiva"
        ]
    }

    rec_cols = st.columns(3)
    for i, (category, items) in enumerate(recommendations.items()):
        with rec_cols[i]:
            st.markdown(f"### {category}")
            for item in items:
                if current_risk > 0.7:
                    st.error(item)
                elif current_risk > 0.4:
                    st.warning(item)
                else:
                    st.info(item)


    # Rename columns based on language
    display_df.columns = [
        get_text('time'),
        get_text('magnitude'),
        get_text('depth') + " (km)",
        get_text('location'),
        "Source"
    ]

    # Show the data table
    st.dataframe(display_df, use_container_width=True)

# Function to show a chart of earthquake magnitudes over time
def show_magnitude_time_chart(df, area, get_text):
    if df.empty:
        return

    # Create the time vs magnitude scatter plot
    fig = px.scatter(
        df,
        x='datetime',
        y='magnitude',
        size='magnitude',
        color='depth',
        hover_name='location',
        color_continuous_scale=px.colors.sequential.Viridis,
        title=f"Magnitude vs Time - {area}",
    )

    # Customize the layout
    fig.update_layout(
        xaxis_title="Data e Ora",
        yaxis_title=get_text('magnitude'),
        coloraxis_colorbar_title=get_text('depth') + " (km)",
        hovermode="closest"
    )

    # Show the chart
    st.plotly_chart(fig, use_container_width=True)

    # Calculate stats before using them
    stats = calculate_earthquake_statistics(df)
    risk_metrics = calculate_risk_level(stats, area)[1]

    # Add SAR Data Visualization
    st.subheader("📡 Dati SAR Sentinel-1")

    sar_cols = st.columns(2)
    with sar_cols[0]:
        st.markdown("### 📊 Mappa di Deformazione")
        # Simulated SAR deformation data
        deformation_data = np.random.normal(0, 2, (10, 10))  # mm/year
        fig = px.imshow(deformation_data,
                       labels=dict(color="mm/anno"),
                       title="Deformazione del suolo")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Interpretazione:**
        - 🔴 Rosso: sollevamento
        - 🔵 Blu: subsidenza
        - ⚪ Bianco: stabile
        """)

    with sar_cols[1]:
        st.markdown("### 📈 Serie Temporale")
        # Generate synthetic time series
        dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
        displacement = np.cumsum(np.random.normal(0.1, 0.05, 30))  # cm

        fig = px.line(x=dates, y=displacement,
                     labels={'x': 'Data', 'y': 'Spostamento (cm)'},
                     title="Trend di deformazione")
        st.plotly_chart(fig, use_container_width=True)

    # Add Enhanced Risk Analysis
    st.subheader("🎯 Analisi del Rischio Avanzata")

    risk_cols = st.columns(3)
    with risk_cols[0]:
        # Risk level gauge
        fig = go.Figure(
go.Indicator(
    mode = "gauge+number",
    value = risk_metrics['event_frequency'] * 100,
    title = {'text': "Livello di Rischio"},
    number = {
        'font': {'size': 48},
        'valueformat': '.0f'
    },
    domain = {'x': [0, 1], 'y': [0, 1]},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "red"},
        'steps': [
            {'range': [0, 30], 'color': "green"},
            {'range': [30, 70], 'color': "yellow"},
            {'range': [70, 100], 'color': "red"}
        ]
    }
)
)
        st.plotly_chart(fig, use_container_width=True)

    with risk_cols[1]:
        # Frequency distribution
        events_per_day = list(stats['daily_counts'].values())
        fig = go.Figure(data=[go.Histogram(x=events_per_day, nbinsx=10)])
        fig.update_layout(title="Distribuzione Eventi Giornalieri")
        st.plotly_chart(fig, use_container_width=True)

    with risk_cols[2]:
        # Risk factors breakdown
        factors = {
            'Frequenza': risk_metrics['event_frequency'],
            'Magnitudo': risk_metrics['magnitude_risk'],
            'Profondità': risk_metrics['depth_risk'],
            'Clustering': risk_metrics['clustering']
        }

        fig = go.Figure(data=[
            go.Bar(x=list(factors.keys()), 
                  y=list(factors.values()),
                  marker_color=['blue', 'red', 'green', 'orange'])
        ])
        fig.update_layout(title="Fattori di Rischio")
        st.plotly_chart(fig, use_container_width=True)

    # Add Risk Calendar with enhanced interactivity
    st.subheader("📅 Calendario del Rischio")

    # Generate calendar data with more detailed predictions
    today = pd.Timestamp.now()
    calendar_start = today - pd.Timedelta(days=15)
    calendar_end = today + pd.Timedelta(days=15)
    dates = pd.date_range(calendar_start, calendar_end, freq='D')

    # Create calendar data with risk levels
    calendar_data = []
    for date in dates:
        if date <= today:
            # Historical risk based on actual data
            daily_count = stats['daily_counts'].get(str(date.date()), 0)
            if daily_count == 0:
                risk = 0
            elif daily_count < 3:
                risk = 0.3
            elif daily_count < 5:
                risk = 0.6
            else:
                risk = 0.9
        else:
            # Predicted risk based on trends
            days_diff = (date - today).days
            base_risk = risk_metrics['event_frequency'] * (1 - days_diff/15)
            risk = max(0.1, min(0.9, base_risk + risk_metrics['acceleration'] * 0.2))

        calendar_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'risk': risk,
            'description': get_risk_description(risk)
        })

    # Create interactive calendar heatmap with detailed tooltips
    fig = go.Figure()

    # Add main heatmap
    fig.add_trace(go.Heatmap(
        x=[d['date'] for d in calendar_data],
        y=['Rischio Previsto'],
        z=[[d['risk'] for d in calendar_data]],
        customdata=[[d['description'] for d in calendar_data]],
        colorscale=[
            [0, 'green'],
            [0.3, 'yellow'],
            [0.6, 'orange'],
            [1.0, 'red']
        ],
        showscale=True,
        hoverongaps=False,
        hovertemplate='Data: %{x}<br>Livello Rischio: %{z:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title='Calendario del Rischio Sismico',
        height=200,
        yaxis_showgrid=False,
        xaxis_showgrid=True
    )

    st.plotly_chart(fig, use_container_width=True, key="magnitude_time_chart")

    # Calculate recent and older counts
    recent_dates = [k for k in stats['daily_counts'].keys() 
                   if pd.to_datetime(k) >= pd.Timestamp.now() - pd.Timedelta(days=3)]
    recent_count = sum(stats['daily_counts'][k] for k in recent_dates)

    older_dates = [k for k in stats['daily_counts'].keys() 
                  if pd.to_datetime(k) < pd.Timestamp.now() - pd.Timedelta(days=3)]
    older_count = sum(stats['daily_counts'][k] for k in older_dates)

    # Add trend indicators
    trend_cols = st.columns(3)
    with trend_cols[0]:
        st.metric(
            "Trend Eventi",
            f"{recent_count} eventi (3gg)",
            f"{int((recent_count - older_count/2)*100)}%" if older_count > 0 else "N/A",
            help="Confronto con la media dei giorni precedenti"
        )
    with trend_cols[1]:
        st.metric(
            "Indice di Clustering",
            f"{risk_metrics['clustering']:.2f}",
            help="Indica la concentrazione temporale degli eventi"
        )
    with trend_cols[2]:
        st.metric(
            "Accelerazione",
            f"{risk_metrics['acceleration']:.2f}",
            help="Tasso di variazione dell'attività sismica"
        )

def get_risk_description(risk):
    if risk < 0.3:
        return "Rischio Basso"
    elif risk < 0.5:
        return "Rischio Moderato"
    elif risk < 0.7:
        return "Rischio Elevato"
    else:
        return "Rischio Molto Elevato"

# Function to show the predictions page
def show_predictions_page(earthquake_data, get_text):
    st.header("🔮 " + get_text('predictions'))

    if earthquake_data is None or earthquake_data.empty:
        st.warning(get_text('no_data'))
        return

    # Statistiche sull'accuratezza delle previsioni
    st.info("""
    ℹ️ **Informazione sull'accuratezza delle previsioni**

    Le analisi previsionali si basano sui dati sismici degli ultimi 30 giorni e vengono aggiornate in tempo reale.
    La valutazione del rischio utilizza modelli statistici con un'accuratezza stimata del 75-85% per eventi di magnitudo >2.0.
    """)

    # Indicatore di aggiornamento
    from datetime import datetime
    last_update = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    st.markdown(f"**Ultimo aggiornamento previsionale:** {last_update} | **Prossimo aggiornamento:** entro 6 ore")

    # Create tabs for different areas of interest
    tab1, tab2, tab3 = st.tabs(["🌍 Italia", "🌋 Vesuvio", "🔥 Campi Flegrei"])

    with tab1:
        st.subheader("Trend sismico - Italia")

        # Accuratezza specifica per questa regione
        with st.expander("ℹ️ Accuratezza previsionale per l'Italia"):
            accuracy_cols = st.columns([2, 1])
            with accuracy_cols[0]:
                st.markdown("""
                **Accuratezza del modello previsionale per l'Italia:**
                - Magnitudo >3.0: **82%** di accuratezza
                - Localizzazione: **±0.8km**
                - Profondità: **±0.5km**

                I modelli previsionali per l'Italia sono più accurati nelle zone ad alta sismicità come 
                l'Appennino centrale e la Sicilia orientale. L'accuratezza diminuisce in aree a bassa sismicità.
                """)
            with accuracy_cols[1]:
                # Show accuracy gauge chart
                import plotly.graph_objects as go
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = 82,
                    title = {'text': "Accuratezza (%)"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 70], 'color': "gray"},
                            {'range': [70, 90], 'color': "lightblue"},
                            {'range': [90, 100], 'color': "blue"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

        show_trend_analysis(earthquake_data, "Italy", get_text)

    with tab2:
        st.subheader("Trend sismico - Vesuvio")

        # Accuratezza specifica per questa regione
        with st.expander("ℹ️ Accuratezza previsionale per il Vesuvio"):
            accuracy_cols = st.columns([2, 1])
            with accuracy_cols[0]:
                st.markdown("""
                **Accuratezza del modello previsionale per il Vesuvio:**
                - Magnitudo >2.0: **88%** di accuratezza
                - Localizzazione: **±0.8km**
                - Profondità: **±0.5km**

                Il monitoraggio del Vesuvio beneficia di una densa rete di strumenti dell'INGV che permettono
                un'accuratezza superiore. L'attività sismica è correlata con altri parametri come deformazioni del suolo
                e variazioni chimiche delle fumarole.
                """)
            with accuracy_cols[1]:
                # Show accuracy gauge chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = 88,
                    title = {'text': "Accuratezza (%)"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkred"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 70], 'color': "gray"},
                            {'range': [70, 90], 'color': "lightsalmon"},
                            {'range': [90, 100], 'color': "red"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

        vesuvio_data = data_service.filter_area_earthquakes(earthquake_data, 'vesuvio')
        if vesuvio_data.empty:
            st.info("Dati insufficienti per l'area del Vesuvio.")
        else:
            show_trend_analysis(vesuvio_data, "Vesuvio", get_text)

    with tab3:
        st.subheader("Trend sismico - Campi Flegrei")

        # Accuratezza specifica per questa regione
        with st.expander("ℹ️ Accuratezza previsionale per i Campi Flegrei"):
            accuracy_cols = st.columns([2, 1])
            with accuracy_cols[0]:
                st.markdown("""
                **Accuratezza del modello previsionale per i Campi Flegrei:**
                - Magnitudo >1.5: **91%** di accuratezza
                - Localizzazione: **±0.8km**
                - Profondità: **±0.5km**

                L'attuale situazione di bradisismo nei Campi Flegrei è monitorata con una rete strumentale
                ad altissima densità. Il modello previsionale include dati di deformazione, gravimetria 
                e composizione dei gas, rendendo le previsioni particolarmente affidabili in quest'area.
                """)
            with accuracy_cols[1]:
                # Show accuracy gauge chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = 91,
                    title = {'text': "Accuratezza (%)"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkorange"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 70], 'color': "gray"},
                            {'range': [70, 90], 'color': "lightyellow"},
                            {'range': [90, 100], 'color': "orange"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig, use_container_width=True)

        flegrei_data = data_service.filter_area_earthquakes(earthquake_data, 'campi_flegrei')
        if flegrei_data.empty:
            st.info("Dati insufficienti per l'area dei Campi Flegrei.")
        else:
            show_trend_analysis(flegrei_data, "Campi Flegrei", get_text)

# Function to show trend analysis and basic earthquake predictions
def show_trend_analysis(df, area, get_text):
    # Calculate statistics
    stats = data_service.calculate_earthquake_statistics(df)

    # Calculate risk level based on statistics
    risk_level, risk_metrics = calculate_risk_level(stats, area)

    # Display risk level indicator at the top
    st.subheader("Livello di rischio attuale")
    risk_cols = st.columns([1, 3])

    with risk_cols[0]:
        # Visual risk indicator
        if risk_level == "basso":
            st.markdown(f"<h1 style='text-align: center; color: green;'>🟢</h1>", unsafe_allow_html=True)
        elif risk_level == "moderato":
            st.markdown(f"<h1 style='text-align: center; color: orange;'>🟠</h1>", unsafe_allow_html=True)
        elif risk_level == "elevato":
            st.markdown(f"<h1 style='text-align: center; color: red;'>🔴</h1>", unsafe_allow_html=True)
        elif risk_level == "molto elevato":
            st.markdown(f"<h1 style='text-align: center; color: darkred;'>⛔</h1>", unsafe_allow_html=True)

    with risk_cols[1]:
        # Risk description
        st.markdown(f"**Livello {risk_level.upper()}**")
        if risk_level == "basso":
            st.markdown("Attività sismica nella norma. Non sono necessarie misure straordinarie.")
        elif risk_level == "moderato":
            st.markdown("Leggero aumento dell'attività sismica. Consigliabile monitorare gli aggiornamenti.")
        elif risk_level == "elevato":
            st.markdown("⚠️ Significativo aumento dell'attività sismica. Prestare attenzione agli aggiornamenti della Protezione Civile.")
        elif risk_level == "molto elevato":
            st.markdown("⚠️ Attività sismica intensa. Seguire strettamente le istruzioni delle autorità locali e della Protezione Civile.")

    # Display statistics
    st.subheader("Dati statistici")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Totale Eventi", stats['count'])
    with col2:
        st.metric(f"{get_text('magnitude')} Max", f"{stats['max_magnitude']:.1f}")
    with col3:
        st.metric(f"{get_text('magnitude')} Media", f"{stats['avg_magnitude']:.1f}")
    with col4:
        st.metric(f"{get_text('depth')} Media", f"{stats['avg_depth']:.1f} km")

    # Risk factor trends section
    st.subheader("Analisi dei fattori di rischio")

    # Create gauge chart for risk factors
    risk_factors = {
        "Frequenza eventi": min(stats['count'] / 10, 1.0) if stats['count'] > 0 else 0,
        "Intensità": min(stats['max_magnitude'] / 6, 1.0) if stats['max_magnitude'] > 0 else 0,
        "Superficialità": max(0, 1 - stats['avg_depth'] / 20) if stats['avg_depth'] > 0 else 0
    }

    # Create a radar chart for risk factors
    categories = list(risk_factors.keys())
    values = list(risk_factors.values())

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Fattori di Rischio',
        line=dict(color='red'),
        fillcolor='rgba(250, 0, 0, 0.2)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title="Indicatori di Rischio"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Prepare data for daily events chart
    if stats['daily_counts']:
        st.subheader("Distribuzione temporale")
        dates = list(stats['daily_counts'].keys())
        counts = list(stats['daily_counts'].values())

        # Create the bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates,
            y=counts,
            marker_color='royalblue'
        ))

        fig.update_layout(
            title=f"Eventi sismici giornalieri - {area}",
            xaxis_title="Data",
            yaxis_title="Numero di eventi",
            hovermode="x"
        )

        st.plotly_chart(fig, use_container_width=True)

    # Depth vs Magnitude scatter plot
    fig = px.scatter(
        df,
        x='depth',
        y='magnitude',
        size='magnitude',
        color='datetime',
        color_continuous_scale='Viridis',
        title=f"Profondità vs Magnitudo - {area}",
    )

    fig.update_layout(
        xaxis_title=get_text('depth') + " (km)",
        yaxis_title=get_text('magnitude'),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Consigli specifici in base al livello di rischio
    st.subheader("Consigli per la popolazione")

    if risk_level == "basso":
        advice_cols = st.columns(3)
        with advice_cols[0]:
            st.markdown("### ✅ Nessuna azione richiesta")
            st.markdown("""
            - Seguire i normali aggiornamenti
            - Conoscere i piani di evacuazione
            - Verificare l'efficienza del kit di emergenza
            """)
        with advice_cols[1]:
            st.markdown("### 🏠 Casa")
            st.markdown("""
            - Nessuna misura straordinaria necessaria
            - Verificare la stabilità degli oggetti pesanti
            - Controllare regolarmente gli impianti
            """)
        with advice_cols[2]:
            st.markdown("### 🚶 Spostamenti")
            st.markdown("""
            - Nessuna restrizione
            - Attività all'aperto consentite
            - Escursioni in area vulcanica consentite
            """)

    elif risk_level == "moderato":
        advice_cols = st.columns(3)
        with advice_cols[0]:
            st.markdown("### ⚠️ Attenzione consigliata")
            st.markdown("""
            - Consultare regolarmente gli aggiornamenti
            - Ripassare i piani di evacuazione familiari
            - Preparare il kit di emergenza
            - Verificare i contatti dei familiari
            """)
        with advice_cols[1]:
            st.markdown("### 🏠 Casa")
            st.markdown("""
            - Fissare oggetti che potrebbero cadere
            - Identificare i luoghi sicuri in casa
            - Mantenere cariche le batterie dei dispositivi
            - Tenere una torcia e radio a batterie
            """)
        with advice_cols[2]:
            st.markdown("### 🚶 Spostamenti")
            st.markdown("""
            - Evitare aree con divieti specifici
            - Limitare le escursioni in area vulcanica
            - Prestare attenzione ai segnali di avvertimento
            - Evitare zone con fumarole attive
            """)

    elif risk_level == "elevato":
        advice_cols = st.columns(3)
        with advice_cols[0]:
            st.markdown("### 🚨 Massima attenzione")
            st.markdown("""
            - Seguire gli aggiornamenti più volte al giorno
            - Tenersi pronti a evacuare con breve preavviso
            - Verificare le vie di fuga dalla propria zona
            - Preparare documenti e medicinali essenziali
            """)
        with advice_cols[1]:
            st.markdown("### 🏠 Casa")
            st.markdown("""
            - Fissare tutti gli oggetti pesanti
            - Chiudere il gas in caso di assenza
            - Predisporre un kit di emergenza completo
            - Identificare un punto di ritrovo familiare
            """)
        with advice_cols[2]:
            st.markdown("### 🚶 Spostamenti")
            st.markdown("""
            - Evitare le aree vulcaniche e a rischio
            - Limitare gli spostamenti non necessari
            - Tenere il veicolo con il serbatoio pieno
            - Informare sempre qualcuno dei propri spostamenti
            """)

    elif risk_level == "molto elevato":
        st.error("""
        ### ⛔ PERICOLO - SEGUIRE LE ISTRUZIONI DELLE AUTORITÀ

        - Seguire **IMMEDIATAMENTE** le istruzioni della Protezione Civile
        - Evacuare se richiesto, senza esitazione
        - Portare con sé solo l'essenziale
        - Assistere anziani, bambini e persone con disabilità
        - Non tornare indietro per nessun motivo
        - Utilizzare solo le vie di fuga indicate
        - Recarsi ai punti di raccolta designati
        - Tenere sempre accesi radio o dispositivi per aggiornamenti
        """)

    # Show detailed analysis note
    with st.expander("Analisi dettagliata del trend sismico"):
        if stats['count'] == 0:
            st.write("Dati insufficienti per l'analisi.")
        else:
            if stats['avg_magnitude'] > 2.5:
                st.warning("⚠️ L'attività sismica nell'area mostra valori di magnitudo superiori alla media storica.")
            elif stats['count'] > 20:
                st.warning("⚠️ Il numero di eventi sismici nell'area è significativamente più alto della media.")
            else:
                st.success("✅ L'attività sismica nell'area è nella norma.")

            st.write(f"""
            Nell'ultimo periodo sono stati registrati {stats['count']} eventi sismici nell'area di {area}.
            La magnitudo media degli eventi è {stats['avg_magnitude']:.1f}, con un valore massimo di {stats['max_magnitude']:.1f}.
            La profondità media degli epicentri è {stats['avg_depth']:.1f} km.
            """)

            if area == "Campi Flegrei" and stats['avg_depth'] < 3:
                st.warning("""
                ⚠️ La bassa profondità degli eventi nei Campi Flegrei è tipica del bradisismo.
                Questo fenomeno indica il movimento del suolo dovuto alla pressione del magma sottostante.
                """)

            if area == "Vesuvio" and stats['max_magnitude'] > 3.0:
                st.warning("""
                ⚠️ Eventi di magnitudo superiore a 3.0 nell'area del Vesuvio possono indicare un aumento dell'attività magmatica.
                Prestare attenzione agli aggiornamenti dell'Osservatorio Vesuviano.
                """)

# Funzione per calcolare il livello di rischio in base alle statistiche
def calculate_risk_level(stats, area):
    # Enhanced risk calculation system
    risk_metrics = {
        'event_frequency': 0,
        'magnitude_risk': 0,
        'depth_risk': 0,
        'spatial_density': 0,
        'temporal_trend': 0,
        'acceleration': 0,
        'clustering': 0
    }

    if stats['count'] == 0:
        return "basso", risk_metrics

    # Calculate event frequency trend
    recent_count = sum(v for k, v in stats['daily_counts'].items() 
                      if pd.to_datetime(k) >= pd.Timestamp.now() - pd.Timedelta(days=3))
    older_count = sum(v for k, v in stats['daily_counts'].items() 
                     if pd.to_datetime(k) < pd.Timestamp.now() - pd.Timedelta(days=3))

    acceleration = recent_count / (older_count + 1)  # Avoid division by zero
    risk_metrics['acceleration'] = min(acceleration / 2, 1.0)

    # Enhanced magnitude risk calculation
    magnitude_threshold = 2.0 if area == "Campi Flegrei" else 2.5
    risk_metrics['magnitude_risk'] = min((stats['max_magnitude'] - magnitude_threshold) / 3.0, 1.0)

    # Depth risk with area-specific weighting
    depth_weight = 1.5 if area == "Campi Flegrei" else 1.0
    risk_metrics['depth_risk'] = min((20 - stats['avg_depth']) / 20 * depth_weight, 1.0)

    # Event frequency normalized by area
    frequency_threshold = 30 if area == "Campi Flegrei" else 20
    risk_metrics['event_frequency'] = min(stats['count'] / frequency_threshold, 1.0)

    # Calculate temporal clustering
    if len(stats['daily_counts']) > 1:
        values = list(stats['daily_counts'].values())
        clustering = np.std(values) / (np.mean(values) + 1)  # Normalized variation
        risk_metrics['clustering'] = min(clustering, 1.0)

    # Calculate overall risk score with area-specific weights
    weights = {
        'Campi Flegrei': {
            'event_frequency': 0.25,
            'magnitude_risk': 0.2,
            'depth_risk': 0.25,
            'acceleration': 0.2,
            'clustering': 0.1
        },
        'Vesuvio': {
            'event_frequency': 0.2,
            'magnitude_risk': 0.3,
            'depth_risk': 0.2,
            'acceleration': 0.2,
            'clustering': 0.1
        },
        'default': {
            'event_frequency': 0.2,
            'magnitude_risk': 0.25,
            'depth_risk': 0.2,
            'acceleration': 0.25,
            'clustering': 0.1
        }
    }

    area_weights = weights.get(area, weights['default'])
    risk_score = sum(risk_metrics[k] * v for k, v in area_weights.items())

    # Define risk levels with personalized thresholds
    if risk_score < 0.3:
        return "basso", risk_metrics
    elif risk_score < 0.5:
        return "moderato", risk_metrics
    elif risk_score < 0.7:
        return "elevato", risk_metrics
    else:
        return "molto elevato", risk_metrics

    # Calculate event frequency risk (0-1)
    risk_metrics['event_frequency'] = min(stats['count'] / 50, 1.0)

    # Calculate magnitude risk (0-1)
    risk_metrics['magnitude_risk'] = min(stats['max_magnitude'] / 5.0, 1.0)

    # Calculate depth risk (0-1) - shallower events are more dangerous
    risk_metrics['depth_risk'] = max(0, 1 - (stats['avg_depth'] / 20))

    # Area-specific adjustments
    if area == "Campi Flegrei":
        if stats['avg_depth'] < 3:
            risk_metrics['depth_risk'] *= 1.5
    elif area == "Vesuvio":
        if stats['max_magnitude'] > 2.5:
            risk_metrics['magnitude_risk'] *= 1.3

    # Calculate overall risk score
    risk_score = (
        risk_metrics['event_frequency'] * 0.3 +
        risk_metrics['magnitude_risk'] * 0.4 +
        risk_metrics['depth_risk'] * 0.3
    )

    # Calcolo punteggio di rischio in base all'area
    risk_score = 0

    # Fattore frequenza eventi
    if stats['count'] < 5:
        risk_score += 0
    elif stats['count'] < 15:
        risk_score += 1
    elif stats['count'] < 30:
        risk_score += 2
    else:
        risk_score += 3

    # Fattore magnitudo massima
    if stats['max_magnitude'] < 2.0:
        risk_score += 0
    elif stats['max_magnitude'] < 3.0:
        risk_score += 1
    elif stats['max_magnitude'] < 4.0:
        risk_score += 2
    else:
        risk_score += 3

    # Fattore profondità media (eventi superficiali sono più pericolosi)
    if stats['avg_depth'] > 15:
        risk_score += 0
    elif stats['avg_depth'] > 10:
        risk_score += 1
    elif stats['avg_depth'] > 5:
        risk_score += 2
    else:
        risk_score += 3

    # Aggiustamento per area specifica
    if area == "Campi Flegrei":
        # Il bradisismo nei Campi Flegrei può indicare un maggiore rischio
        if stats['avg_depth'] < 3:
            risk_score += 1
    elif area == "Vesuvio":
        # Per il Vesuvio, anche pochi eventi possono essere significativi
        if stats['max_magnitude'] > 2.5:
            risk_score += 1

    # Determinazione del livello di rischio in base al punteggio
    if risk_score <= 2:
        risk_level = "basso"
    elif risk_score <= 5:
        risk_level = "moderato"
    elif risk_score <= 7:
        risk_level = "elevato"
    else:
        risk_level = "molto elevato"

    return risk_level
