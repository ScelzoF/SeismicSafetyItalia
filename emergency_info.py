import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd

# Function to show emergency information and guidelines
def show_emergency_page(get_text):
    st.header("🚨 " + get_text('emergency'))
    
    # Create tabs for different emergency information
    tab, tab2, tab3 = st.tabs(["📝 Linee Guida", "🚗 Vie di Fuga", "🏥 Punti di Soccorso"])
    
    with tab:
        show_emergency_guidelines()
        
    with tab2:
        show_evacuation_routes()
        
    with tab3:
        show_emergency_centers()

# Function to display earthquake emergency guidelines
def show_emergency_guidelines():
    st.subheader("Cosa fare in caso di terremoto")
    
    # Before an earthquake
    with st.expander("PRIMA del terremoto", expanded=True):
        st.markdown("""
        ### Preparazione
        - **Informati** sulla classificazione sismica del tuo comune
        - **Assicurati** che la tua casa rispetti le norme antisismiche
        - **Identifica** i punti sicuri dell'abitazione: muri portanti, travi, architravi
        - **Prepara** un kit di emergenza con:
            - Acqua e cibo non deperibile
            - Torcia elettrica e batterie di riserva
            - Kit di primo soccorso e medicinali essenziali
            - Radio a batterie
            - Denaro contante e documenti importanti
        - **Stabilisci** un piano di emergenza familiare con punto di ritrovo
        """)
    
    # During an earthquake
    with st.expander("DURANTE il terremoto", expanded=True):
        st.markdown("""
        ### Se sei in un luogo chiuso:
        - **Mantieni la calma**
        - **Non precipitarti fuori**, rimani dove sei fino al termine della scossa
        - **Riparati** sotto un tavolo robusto, nel vano di una porta inserita in un muro portante o sotto una trave
        - **Allontanati** da finestre, mobili pesanti, scale, ascensori
        - **Non usare** fiamme libere (accendini, fiammiferi) per evitare fughe di gas
        
        ### Se sei all'aperto:
        - **Allontanati** da edifici, alberi, lampioni, linee elettriche
        - **Cerca** uno spazio aperto
        - **Non avvicinarti** alle spiagge, un terremoto può generare tsunami
        
        ### Se sei in auto:
        - **Fermati** lontano da edifici, ponti, cavalcavia
        - **Rimani in auto** con cinture allacciate fino al termine della scossa
        """)
    
    # After an earthquake
    with st.expander("DOPO il terremoto", expanded=True):
        st.markdown("""
        ### Dopo la scossa:
        - **Assicurati** delle condizioni di chi ti circonda e presta i primi soccorsi se necessario
        - **Esci con prudenza** indossando scarpe (potrebbero esserci detriti)
        - **Raggiungi** gli spazi aperti
        - **Verifica** lo stato delle utenze (acqua, luce, gas)
        - **Chiudi** il gas e stacca la corrente
        - **Limita l'uso** del telefono cellulare
        - **Segui** le indicazioni delle autorità
        
        ### Zone sicure:
        - Aree aperte lontane da edifici e strutture pericolanti
        - Punti di raccolta designati
        - Aree di emergenza predisposte dalla Protezione Civile
        """)
    
    # Special considerations for Phlegraean Fields/Campi Flegrei
    with st.expander("RISCHIO BRADISISMO (Campi Flegrei)", expanded=True):
        st.markdown("""
        ### Bradisismo nei Campi Flegrei:
        - Il bradisismo è il fenomeno di innalzamento o abbassamento del suolo tipico dell'area flegrea
        - Questo fenomeno può causare sciami sismici anche senza eruzioni vulcaniche
        
        ### Segnali da monitorare:
        - Crepe nei muri o pavimenti delle abitazioni
        - Difficoltà nell'apertura/chiusura di porte e finestre
        - Rumori anomali (boati)
        - Aumento della temperatura del suolo
        
        ### Cosa fare:
        - **Segnala** alle autorità la comparsa di questi fenomeni
        - **Segui** le comunicazioni ufficiali della Protezione Civile
        - **Conosci** il piano di evacuazione comunale
        - **Mantieni** aggiornati i contatti con i centri operativi locali
        """)
    
    # Official sources
    st.subheader("Fonti ufficiali")
    col, col2, col3 = st.columns(3)
    
    with col:
        st.markdown("[Protezione Civile](https://www.protezionecivile.gov.it/it/rischio/rischio-sismico)")
    with col2:
        st.markdown("[INGV](https://www.ingv.it/)")
    with col3:
        st.markdown("[Osservatorio Vesuviano](https://www.ov.ingv.it/)")

# Function to display evacuation routes
def show_evacuation_routes():
    st.subheader("Vie di Fuga e Zone di Evacuazione")
    
    # Create tabs for different areas
    area_tab, area_tab2 = st.tabs(["🌋 Area Vesuvio", "🔥 Campi Flegrei"])
    
    with area_tab:
        st.markdown("""
        ### Piano di evacuazione del Vesuvio
        
        Il piano di evacuazione per il Vesuvio prevede una divisione del territorio in zone a rischio:
        
        - **Zona Rossa**: area da evacuare cautelativamente prima dell'inizio dell'eruzione
        - **Zona Gialla**: area esposta alla significativa ricaduta di ceneri vulcaniche
        - **Zona Blu**: area esposta al rischio di alluvionamenti e frane
        
        In caso di allarme, la popolazione dovrà seguire le vie di fuga designate verso i punti di raccolta, da dove sarà trasferita nelle aree di accoglienza fuori dalla zona rossa.
        """)
        
        # Show Vesuvio evacuation map
        vesuvio_map = folium.Map(location=[40.82, 4.42], zoom_start=, tiles="CartoDB positron")
        
        # Add zone colored overlays
        folium.Circle(
            location=[40.85, 4.428],  # Mt. Vesuvius center
            radius=0000,  # Red zone radius (0km)
            color='red',
            fill=True,
            fill_opacity=0.2,
            popup="Zona Rossa - Evacuazione obbligatoria"
        ).add_to(vesuvio_map)
        
        folium.Circle(
            location=[40.85, 4.428],  # Mt. Vesuvius center
            radius=5000,  # Yellow zone radius (5km)
            color='yellow',
            fill=True,
            fill_opacity=0.,
            popup="Zona Gialla - Possibile caduta ceneri"
        ).add_to(vesuvio_map)
        
        # Main evacuation routes
        routes = [
            {"name": "A3 Napoli-Salerno", "coords": [[40.85, 4.27], [40.65, 4.47]]},
            {"name": "A6 Napoli-Canosa", "coords": [[40.9, 4.32], [4.05, 4.55]]},
            {"name": "SS268", "coords": [[40.8, 4.34], [40.79, 4.50]]}
        ]
        
        for route in routes:
            folium.PolyLine(
                route["coords"],
                color='green',
                weight=4,
                opacity=0.8,
                popup=route["name"]
            ).add_to(vesuvio_map)
        
        # Meeting points
        meeting_points = [
            {"name": "Punto di Raccolta Torre del Greco", "location": [40.78, 4.37]},
            {"name": "Punto di Raccolta Portici", "location": [40.82, 4.35]},
            {"name": "Punto di Raccolta Ercolano", "location": [40.80, 4.36]},
            {"name": "Punto di Raccolta San Giorgio", "location": [40.83, 4.33]},
            {"name": "Punto di Raccolta Somma Vesuviana", "location": [40.87, 4.43]}
        ]
        
        for point in meeting_points:
            folium.Marker(
                location=point["location"],
                popup=point["name"],
                icon=folium.Icon(color='green', icon='flag')
            ).add_to(vesuvio_map)
        
        folium_static(vesuvio_map)
        
        st.markdown("""
        ### Fasi dell'evacuazione
        
        . **Fase di attenzione**: aumento dell'attività vulcanica, potenziamento del monitoraggio
        2. **Fase di preallarme**: ulteriore intensificazione dei fenomeni, evacuazione preventiva di ospedali e case di cura
        3. **Fase di allarme**: imminente eruzione, evacuazione completa della zona rossa
        
        ### Comportamento durante l'evacuazione
        
        - Segui le indicazioni della Protezione Civile e delle autorità locali
        - Porta con te solo l'essenziale e i documenti importanti
        - Chiudi gas, acqua e luce prima di lasciare l'abitazione
        - Raggiungi i punti di raccolta utilizzando mezzi propri o trasporti pubblici
        - Non tornare indietro per nessun motivo
        """)
    
    with area_tab2:
        st.markdown("""
        ### Piano di evacuazione dei Campi Flegrei
        
        Il piano di evacuazione per i Campi Flegrei prevede una divisione del territorio in zone a rischio:
        
        - **Zona Rossa**: area da evacuare cautelativamente prima dell'inizio dell'eruzione
        - **Zona Gialla**: area esposta alla significativa ricaduta di ceneri vulcaniche
        
        In caso di allarme, la popolazione dovrà seguire le vie di fuga designate verso i punti di primo intervento e successivamente verso le aree di accoglienza predisposte fuori dalla zona rossa.
        """)
        
        # Show Campi Flegrei evacuation map
        flegrei_map = folium.Map(location=[40.85, 4.4], zoom_start=, tiles="CartoDB positron")
        
        # Add zone colored overlays
        folium.Circle(
            location=[40.83, 4.4],  # Solfatara center
            radius=8000,  # Red zone radius (8km)
            color='red',
            fill=True,
            fill_opacity=0.2,
            popup="Zona Rossa - Evacuazione obbligatoria"
        ).add_to(flegrei_map)
        
        folium.Circle(
            location=[40.83, 4.4],  # Solfatara center
            radius=2000,  # Yellow zone radius (2km)
            color='yellow',
            fill=True,
            fill_opacity=0.,
            popup="Zona Gialla - Possibile caduta ceneri"
        ).add_to(flegrei_map)
        
        # Main evacuation routes
        routes = [
            {"name": "Tangenziale di Napoli", "coords": [[40.85, 4.7], [40.88, 4.25]]},
            {"name": "Via Domitiana", "coords": [[40.82, 4.05], [40.92, 3.95]]},
            {"name": "SS7 Via Appia", "coords": [[40.83, 4.2], [40.9, 4.03]]}
        ]
        
        for route in routes:
            folium.PolyLine(
                route["coords"],
                color='green',
                weight=4,
                opacity=0.8,
                popup=route["name"]
            ).add_to(flegrei_map)
        
        # Meeting points
        meeting_points = [
            {"name": "Punto di Raccolta Pozzuoli", "location": [40.83, 4.]},
            {"name": "Punto di Raccolta Bacoli", "location": [40.80, 4.07]},
            {"name": "Punto di Raccolta Monte di Procida", "location": [40.79, 4.05]},
            {"name": "Punto di Raccolta Quarto", "location": [40.87, 4.5]},
            {"name": "Punto di Raccolta Bagnoli", "location": [40.8, 4.7]}
        ]
        
        for point in meeting_points:
            folium.Marker(
                location=point["location"],
                popup=point["name"],
                icon=folium.Icon(color='green', icon='flag')
            ).add_to(flegrei_map)
        
        folium_static(flegrei_map)
        
        st.markdown("""
        ### Rischio Bradisismo
        
        I Campi Flegrei sono soggetti al fenomeno del bradisismo, un sollevamento o abbassamento del suolo che può causare:
        
        - Sciami sismici
        - Formazione di crepe negli edifici
        - Modifiche alla linea di costa
        - Emissioni di gas
        
        ### Cosa fare in caso di bradisismo
        
        - Segnala immediatamente alle autorità l'apertura di crepe negli edifici
        - Non sostare in edifici danneggiati
        - Tieniti informato tramite i canali ufficiali
        - Segui le indicazioni della Protezione Civile
        """)

# Function to display emergency centers
def show_emergency_centers():
    st.subheader("Punti di Soccorso e Centri Operativi")
    
    # Create tabs for different areas
    area_tab, area_tab2 = st.tabs(["🌋 Area Vesuvio", "🔥 Campi Flegrei"])
    
    with area_tab:
        # Show Vesuvio emergency centers map
        vesuvio_em_map = folium.Map(location=[40.82, 4.42], zoom_start=, tiles="CartoDB positron")
        
        # Add emergency centers
        emergency_centers = [
            {"name": "Ospedale del Mare", "location": [40.86, 4.34], "type": "Ospedale"},
            {"name": "Ospedale Maresca", "location": [40.78, 4.37], "type": "Ospedale"},
            {"name": "COC Torre del Greco", "location": [40.78, 4.36], "type": "Centro Operativo"},
            {"name": "COC Ercolano", "location": [40.80, 4.35], "type": "Centro Operativo"},
            {"name": "COC Portici", "location": [40.82, 4.34], "type": "Centro Operativo"},
            {"name": "Protezione Civile Regionale", "location": [40.84, 4.30], "type": "Protezione Civile"}
        ]
        
        for center in emergency_centers:
            icon_color = 'red' if center["type"] == "Ospedale" else 'blue'
            icon_type = 'plus' if center["type"] == "Ospedale" else 'info-sign'
            
            folium.Marker(
                location=center["location"],
                popup=f"{center['name']} - {center['type']}",
                icon=folium.Icon(color=icon_color, icon=icon_type)
            ).add_to(vesuvio_em_map)
        
        folium_static(vesuvio_em_map)
        
        # List of emergency contacts
        st.subheader("Contatti di emergenza")
        
        emergency_contacts = {
            "Numero Unico Emergenze": "2",
            "Protezione Civile Regionale": "800 232525",
            "INGV - Osservatorio Vesuviano": "08 608",
            "Prefettura di Napoli": "08 7943",
            "Croce Rossa Italiana": "800 06550"
        }
        
        # Display contacts as a table
        contacts_df = pd.DataFrame(list(emergency_contacts.items()), columns=["Ente", "Numero"])
        st.table(contacts_df)
    
    with area_tab2:
        # Show Campi Flegrei emergency centers map
        flegrei_em_map = folium.Map(location=[40.85, 4.4], zoom_start=, tiles="CartoDB positron")
        
        # Add emergency centers
        emergency_centers = [
            {"name": "Ospedale Santa Maria delle Grazie", "location": [40.83, 4.0], "type": "Ospedale"},
            {"name": "Ospedale San Paolo", "location": [40.84, 4.9], "type": "Ospedale"},
            {"name": "COC Pozzuoli", "location": [40.82, 4.2], "type": "Centro Operativo"},
            {"name": "COC Bacoli", "location": [40.80, 4.08], "type": "Centro Operativo"},
            {"name": "COC Quarto", "location": [40.87, 4.5], "type": "Centro Operativo"},
            {"name": "Protezione Civile Regionale", "location": [40.84, 4.30], "type": "Protezione Civile"}
        ]
        
        for center in emergency_centers:
            icon_color = 'red' if center["type"] == "Ospedale" else 'blue'
            icon_type = 'plus' if center["type"] == "Ospedale" else 'info-sign'
            
            folium.Marker(
                location=center["location"],
                popup=f"{center['name']} - {center['type']}",
                icon=folium.Icon(color=icon_color, icon=icon_type)
            ).add_to(flegrei_em_map)
        
        folium_static(flegrei_em_map)
        
        # List of emergency contacts
        st.subheader("Contatti di emergenza")
        
        emergency_contacts = {
            "Numero Unico Emergenze": "2",
            "Protezione Civile Regionale": "800 232525",
            "INGV - Osservatorio Vesuviano": "08 608",
            "Osservatorio del Bradisismo": "08 85577",
            "Prefettura di Napoli": "08 7943",
            "Croce Rossa Italiana": "800 06550"
        }
        
        # Display contacts as a table
        contacts_df = pd.DataFrame(list(emergency_contacts.items()), columns=["Ente", "Numero"])
        st.table(contacts_df)
