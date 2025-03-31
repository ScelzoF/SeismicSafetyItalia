
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

def show():
    st.header("🆘 EMERGENZA - Cosa Fare e Dove Andare")
    st.markdown("In questa sezione trovi informazioni **utili e reali** in caso di emergenza sismica, alluvione o altro evento critico.")

    st.subheader("📍 Punti di raccolta e aree sicure")
    m = folium.Map(location=[41.9028, 12.4964], zoom_start=6)
    points = [
        {"name": "Protezione Civile Roma", "lat": 41.928, "lon": 12.566},
        {"name": "Punto raccolta Napoli", "lat": 40.8518, "lon": 14.2681},
        {"name": "Punto raccolta Catania", "lat": 37.5079, "lon": 15.0830},
    ]
    for p in points:
        folium.Marker(location=[p["lat"], p["lon"]], popup=p["name"], icon=folium.Icon(color="red")).add_to(m)
    st_data = st_folium(m, width=700, height=450)

    st.markdown("""
- **112** - Numero Unico Emergenze
- **115** - Vigili del Fuoco
- **118** - Emergenza Sanitaria
- **800 840 840** - Protezione Civile Nazionale
    """)

    st.subheader("🔗 Link utili")
    st.markdown("""
- [Dipartimento della Protezione Civile](https://rischi.protezionecivile.gov.it/)
- [Istituto Nazionale di Geofisica e Vulcanologia (INGV)](https://www.ingv.it/)
- [Allerta Meteo Regione per Regione](https://allertameteo.regione.liguria.it/)
    """)


    # ================== INTEGRAZIONE - SUDDIVISIONE REGIONALE ==================

    st.markdown("---")
    st.subheader("📍 Emergenze per Regione")

    regioni = ['Campania', 'Sicilia', 'Liguria', 'Abruzzo', 'Emilia-Romagna', 'Lazio', 'Lombardia', 'Veneto', 'Piemonte', 'Toscana', 'Puglia', 'Calabria', 'Sardegna', 'Marche', 'Umbria', 'Basilicata', 'Molise', 'Basilicata', 'Molise', 'Basilicata', 'Molise', 'Trentino-Alto Adige', 'Friuli-Venezia Giulia', "Valle d'Aosta"]
    regione_sel = st.selectbox("Seleziona la tua regione", regioni)

    dati_regioni = {
        "Campania": {
            "criticita": "Rischio vulcanico (Vesuvio, Campi Flegrei), sismico e idrogeologico.",
            "punti_raccolta": "[Piano Emergenza Vesuvio](https://www.regione.campania.it/)",
            "link_utili": "[ARPAC](http://www.arpacampania.it)"
        },
        "Sicilia": {
            "criticita": "Etna attivo, rischio sismico e incendi.",
            "punti_raccolta": "[Protezione Civile Sicilia](http://www.protezionecivilesicilia.it)",
            "link_utili": "[INGV Etna](https://www.ct.ingv.it/)"
        },
        "Liguria": {
            "criticita": "Frane e alluvioni frequenti.",
            "punti_raccolta": "[ARPAL Liguria](https://allertaliguria.regione.liguria.it)",
            "link_utili": "[ISPRA Liguria](https://www.geositi.isprambiente.it)",
        }
        ,
        "Abruzzo": {
    "criticita": "Rischio sismico elevato, frane e alluvioni frequenti.",
    "punti_raccolta": "L'Aquila: Piazza Duomo, Parco del Castello
Teramo: Piazza Martiri, Stadio Comunale
Pescara: Parco Villa Sabucchi, Piazza della Repubblica
Chieti: Piazza San Giustino, Parco Archeologico La Civitella",
    "link_utili": "[Protezione Civile Abruzzo](https://protezionecivile.regione.abruzzo.it/), [ARPA Abruzzo](https://www.arpaabruzzo.it)"
}
        ,
        "Emilia-Romagna": {
            "criticita": "Rischio alluvioni frequente, rischio sismico appenninico.",
            "punti_raccolta": "[Protezione Civile Emilia-Romagna](https://www.protezionecivile.emilia-romagna.it/)",
            "link_utili": "[ARPAE Emilia-Romagna](https://www.arpae.it)"
        }
        ,
        "Lazio": {
            "criticita": "Rischio idrogeologico e sismico, aree vulcaniche nei Colli Albani.",
            "punti_raccolta": "[Protezione Civile Lazio](https://www.protezionecivile.regione.lazio.it/)",
            "link_utili": "[ARPA Lazio](https://www.arpalazio.it)"
        }
        ,
        "Lombardia": {
            "criticita": "Rischio idrogeologico, inondazioni e valanghe in area alpina.",
            "punti_raccolta": "[Protezione Civile Lombardia](https://www.protezionecivile.regione.lombardia.it/)",
            "link_utili": "[ARPA Lombardia](https://www.arpalombardia.it)"
        },
        "Veneto": {
            "criticita": "Alluvioni, frane e rischio idraulico in zone montane.",
            "punti_raccolta": "[Protezione Civile Veneto](https://www.regione.veneto.it/web/protezione-civile)",
            "link_utili": "[ARPAV](https://www.arpa.veneto.it)"
        },
        "Piemonte": {
            "criticita": "Rischio frane e valanghe in area alpina, rischio idrogeologico diffuso.",
            "punti_raccolta": "[Protezione Civile Piemonte](https://www.protezionecivile.piemonte.it/)",
            "link_utili": "[ARPA Piemonte](https://www.arpa.piemonte.it)"
        },
        "Toscana": {
            "criticita": "Rischio alluvionale e idrogeologico, rischio sismico in Appennino.",
            "punti_raccolta": "[Protezione Civile Toscana](https://www.regione.toscana.it/protezionecivile)",
            "link_utili": "[ARPAT Toscana](https://www.arpat.toscana.it)"
        },
        "Puglia": {
            "criticita": "Rischio incendi e sismicità nel Gargano.",
            "punti_raccolta": "[Protezione Civile Puglia](http://www.protezionecivile.puglia.it/)",
            "link_utili": "[ARPA Puglia](https://www.arpa.puglia.it)"
        }
        ,
        
"Calabria": {
    "criticita": "Elevato rischio sismico e frane, dissesto idrogeologico.",
    "punti_raccolta": """Catanzaro: Piazza Prefettura, Parco della Biodiversità
Reggio Calabria: Piazza Italia, Lungomare Falcomatà
Cosenza: Piazza dei Bruzi, Villa Vecchia
Crotone: Piazza Pitagora, Parco Pignera
Vibo Valentia: Piazza Municipio, Parco Urbano""",
    "link_utili": {
        "Protezione Civile Calabria": "https://www.protezionecivilecalabria.it",
        "ARPACAL": "https://www.arpacal.it"
    }
},
        "Sardegna": {
            "criticita": "Incendi boschivi e rischio idrogeologico.",
            "punti_raccolta": "[Protezione Civile Sardegna](https://www.sardegnaambiente.it/protezionecivile/)",
            "link_utili": "[ARPAS](https://www.sarpa.sardegna.it)"
        },
        "Marche": {
            "criticita": "Rischio sismico e idrogeologico nelle zone montane.",
            "punti_raccolta": "[Protezione Civile Marche](https://www.protezionecivile.marche.it/)",
            "link_utili": "[ARPAM](https://www.arpa.marche.it)"
        },
        "Umbria": {
            "criticita": "Rischio sismico elevato, frane in area appenninica.",
            "punti_raccolta": "[Protezione Civile Umbria](https://protezionecivile.regione.umbria.it/)",
            "link_utili": "[ARPA Umbria](https://www.arpa.umbria.it)"
        }
        ,
        "Basilicata": {
            "criticita": "Frane, rischio sismico e incendi.",
            "punti_raccolta": "[Protezione Civile Basilicata](https://protezionecivile.regione.basilicata.it/)",
            "link_utili": "[ARPAB](https://www.arpab.it)"
        },
        "Molise": {
            "criticita": "Rischio sismico e idrogeologico.",
            "punti_raccolta": "[Protezione Civile Molise](https://www.protezionecivile.molise.it/)",
            "link_utili": "[ARPA Molise](https://arpa.molise.it)"
        },
        "Trentino-Alto Adige": {
            "criticita": "Valanghe, frane, rischio sismico minore.",
            "punti_raccolta": "[Protezione Civile Trentino](https://www.protezionecivile.tn.it/)",
            "link_utili": "[ARPAT](https://www.appa.provincia.tn.it)"
        },
        "Friuli-Venezia Giulia": {
            "criticita": "Rischio alluvioni, sismico e idrogeologico.",
            "punti_raccolta": "[Protezione Civile FVG](https://www.protezionecivile.fvg.it/)",
            "link_utili": "[ARPA FVG](https://www.arpa.fvg.it)"
        },
        "Valle d'Aosta": {
            "criticita": "Valanghe, frane, rischio ghiacciai.",
            "punti_raccolta": "[Protezione Civile VdA](https://www.protezionecivile.vda.it/)",
            "link_utili": "[ARPA VdA](https://www.arpa.vda.it)"
        }
    }

    if regione_sel in dati_regioni:
        st.markdown("### 🛑 Criticità territoriali")
        st.markdown(dati_regioni[regione_sel]["criticita"])
        st.markdown("### 📍 Punti di raccolta")
        st.markdown(f"""```\n{dati_regioni[regione_sel]['punti_raccolta']}\n```""")
        st.markdown("### 🔗 Link utili")
        st.markdown(dati_regioni[regione_sel]["link_utili"])


    # ================== EVENTI: COSA FARE / NON FARE ==================

    st.markdown("---")
    st.subheader("⚠️ Cosa fare e non fare in base all'evento")

    evento = st.selectbox("Scegli l'evento", [
        "Terremoto", "Alluvione", "Eruzione Vulcanica",
        "Incendio", "Frana", "Neve", "Tempesta",
        "Emergenza sanitaria", "Blackout", "Emergenza nucleare",
        "Numeri utili"
    ])
        "Terremoto",
        "Alluvione",
        "Eruzione Vulcanica",
        "Numeri utili",
        "Incendio",
        "Frana",
        "Emergenza Sanitaria",
        "Blackout",
        "Neve",
        "Tempesta di vento",
        "Emergenza nucleare"
    ])

    if evento == "Terremoto":
        st.subheader("📌 Terremoto – Cosa fare")
        st.markdown("""\
- Mantieni la calma.
- Riparati sotto un tavolo robusto.
- Allontanati da vetri e oggetti sospesi.
- Dopo la scossa, esci con prudenza.
""")
        st.subheader("❌ Cosa NON fare")
        st.markdown("""\
- Non usare ascensori.
- Non correre verso le uscite.
- Non diffondere panico.
""")
    elif evento == "Alluvione":
        st.subheader("📌 Alluvione – Cosa fare")
        st.markdown("""\
- Salire ai piani alti.
- Evitare cantine o locali interrati.
- Tenere a portata kit di emergenza.
""")
        st.subheader("❌ Cosa NON fare")
        st.markdown("""\
- Non attraversare strade allagate.
- Non toccare apparecchi elettrici bagnati.
""")
    elif evento == "Eruzione Vulcanica":
        "Numeri utili",
        st.subheader("📌 Eruzione – Cosa fare")
        st.markdown("""\
- Seguire le indicazioni della Protezione Civile.
- Indossare mascherine per la cenere.
- Proteggere occhi e vie respiratorie.
""")
        st.subheader("❌ Cosa NON fare")
        st.markdown("""\
- Non restare all’aperto se cade cenere.
- Non usare veicoli se non necessario.
""")
    elif evento == "Numeri utili":
        st.subheader("📞 Numeri di Emergenza")
        st.markdown("""\
- **112** – Numero unico di emergenza
- **118** – Emergenza sanitaria
- **115** – Vigili del Fuoco
- **113** – Polizia
- **1515** – Emergenze ambientali (Corpo Forestale)
- **1522** – Antiviolenza e stalking
- **800 840 840** – Protezione Civile
- **800 861 016** – Centro Antiveleni
""")


    elif evento == "Incendio":
        st.markdown("""🔥 **Cosa fare in caso di incendio:**
- Allontanati rapidamente dalla zona
- Avvisa i soccorsi (115)
- Tieni un panno bagnato su naso e bocca se c'è fumo
- Chiudi le porte dietro di te per rallentare la diffusione del fuoco

🚫 **Cosa NON fare:**
- Non usare ascensori
- Non aprire porte calde
- Non tornare indietro per recuperare oggetti personali
""")
        st.subheader("🔥 Cosa fare in caso di INCENDIO")
        st.markdown("- Allontanarsi immediatamente dalla zona dell’incendio")
        st.markdown("- Coprire naso e bocca con un panno umido")
        st.markdown("- Segnalare l’incendio al 115")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non tentare di spegnere incendi estesi da soli")
        st.markdown("- Non intralciare le vie di fuga")
    elif evento == "Frana":
        st.markdown("""⛰️ **Cosa fare in caso di frana:**
- Allontanati immediatamente dalla zona a rischio
- Avvisa le autorità
- Se sei in auto, evita ponti e pendii

🚫 **Cosa NON fare:**
- Non sostare vicino a versanti instabili
- Non attraversare zone allagate o fangose
""")
        st.subheader("⛰️ Cosa fare in caso di FRANA")
        st.markdown("- Allontanarsi velocemente dalla zona a rischio")
        st.markdown("- Seguire i percorsi di evacuazione indicati")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non sostare sotto pendii o versanti instabili")
    elif evento == "Neve":
        st.markdown("""❄️ **Cosa fare durante forti nevicate:**
- Rimani in casa se possibile
- Tieni scorte di acqua, cibo e coperte
- Controlla gli aggiornamenti meteo e allerta

🚫 **Cosa NON fare:**
- Evita di guidare senza pneumatici adeguati
- Non usare fuochi aperti in ambienti chiusi
""")
        st.subheader("❄️ Cosa fare in caso di NEVE intensa")
        st.markdown("- Evitare spostamenti non necessari")
        st.markdown("- Tenere in auto catene da neve o pneumatici invernali")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non utilizzare mezzi non adeguati")
    elif evento == "Tempesta":
        st.markdown("""🌬️ **Cosa fare durante una tempesta di vento:**
- Rimani al chiuso e chiudi bene porte e finestre
- Allontanati da alberi, cartelloni pubblicitari e strutture precarie
- Se sei in auto, fermati in un'area sicura lontana da oggetti sospesi

🚫 **Cosa NON fare:**
- Non sostare sotto tettoie o vicino a impalcature
- Non camminare vicino a edifici con oggetti pericolanti
""")
        st.markdown("""🌪️ **Cosa fare durante una tempesta:**
- Rimani al chiuso e lontano da finestre
- Disconnetti apparecchi elettrici
- Tieniti informato tramite fonti ufficiali

🚫 **Cosa NON fare:**
- Non ripararti sotto alberi o tettoie instabili
- Non toccare cavi elettrici
""")
        st.subheader("🌪️ Cosa fare in caso di TEMPESTA")
        st.markdown("- Restare in casa, lontani da finestre")
        st.markdown("- Spegnere apparecchi elettrici non necessari")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non uscire se non strettamente necessario")
    elif evento == "Emergenza sanitaria":
        st.markdown("""🏥 **Cosa fare in caso di emergenza sanitaria:**
- Segui le direttive delle autorità sanitarie
- Se hai sintomi gravi, chiama il numero di emergenza 118
- Se possibile, evita di sovraffollare ospedali e pronto soccorso per casi non urgenti

🚫 **Cosa NON fare:**
- Non diffondere notizie non verificate
- Non interrompere trattamenti senza consultare un medico
""")
        st.markdown("""🩺 **Cosa fare in caso di emergenza sanitaria:**
- Segui le istruzioni delle autorità sanitarie
- Indossa mascherina se richiesto
- Isolati in caso di sintomi sospetti

🚫 **Cosa NON fare:**
- Non diffondere notizie false
- Non trascurare i sintomi
""")
        st.subheader("🧪 Cosa fare in caso di EMERGENZA SANITARIA")
        st.markdown("- Seguire le indicazioni delle autorità sanitarie")
        st.markdown("- Indossare DPI se richiesto")
        st.markdown("- Evitare assembramenti")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non diffondere fake news")
    elif evento == "Blackout":
        st.markdown("""💡 **Cosa fare durante un blackout:**
- Usa torce a batteria, non candele
- Disattiva elettrodomestici per evitare sovraccarichi al ritorno della corrente
- Tieni carichi i dispositivi mobili

🚫 **Cosa NON fare:**
- Non aprire inutilmente il frigorifero
- Non utilizzare generatori in ambienti chiusi
""")
        st.subheader("⚫ Cosa fare in caso di BLACKOUT")
        st.markdown("- Usare torce a batteria")
        st.markdown("- Staccare gli elettrodomestici per evitare sbalzi")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non usare candele vicino a materiali infiammabili")
    elif evento == "Emergenza nucleare":
        st.markdown("""☢️ **Cosa fare in caso di emergenza nucleare:**
- Rimani al chiuso e sigilla porte e finestre
- Segui le indicazioni della Protezione Civile
- Assumi iodio solo se consigliato dalle autorità

🚫 **Cosa NON fare:**
- Non uscire finché non è dichiarato sicuro
- Non mangiare alimenti esposti
""")
        st.subheader("☢️ Cosa fare in caso di EMERGENZA NUCLEARE")
        st.markdown("- Chiudersi in casa sigillando porte e finestre")
        st.markdown("- Seguire le indicazioni delle autorità")
        st.markdown("- Sintonizzarsi su canali ufficiali")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non uscire per curiosare")

import requests
import folium
from streamlit_folium import st_folium

# Function to fetch dynamically updated points of collection from an external API
def fetch_dynamically_updated_points():
    api_url = 'https://api.protezionecivile.gov.it/points_of_collection'  # Example URL, modify with real one
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Function to update the map with emergency collection points
def update_emergency_points_on_map(m):
    points = fetch_dynamically_updated_points()
    if points:
        for point in points:
            folium.Marker(
                location=[point['lat'], point['lon']], 
                popup=point['name'],
                icon=folium.Icon(color="blue")
            ).add_to(m)

# Function to fetch dynamic emergency numbers
def fetch_dynamic_emergency_numbers():
    api_url = 'https://api.protezionecivile.gov.it/emergency_numbers'  # Example URL, modify with real one
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"112": "Emergenza Generale", "118": "Emergenza Sanitaria"}

# Function to update emergency numbers on the UI
def update_emergency_numbers():
    emergency_numbers = fetch_dynamic_emergency_numbers()
    st.markdown(f"**112** - {emergency_numbers.get('112', 'Emergenza Generale')}")
    st.markdown(f"**118** - {emergency_numbers.get('118', 'Emergenza Sanitaria')}")

# Main function to display the emergency section
def show():
    st.header("🆘 EMERGENZA - Cosa Fare e Dove Andare")
    st.markdown("In questa sezione trovi informazioni **utili e reali** in caso di emergenza sismica.")
    m = folium.Map(location=[41.9028, 12.4964], zoom_start=6)  # Initial map
    update_emergency_points_on_map(m)  # Add dynamic collection points
    st_data = st_folium(m, width=700, height=450)

    # Show dynamic emergency numbers
    update_emergency_numbers()

import folium
import requests

def update_emergency_points_on_map(m):
    api_url = 'https://api.protezionecivile.gov.it/points_of_collection'  # URL dell'API per i punti di raccolta
    response = requests.get(api_url)
    
    if response.status_code == 200:
        points = response.json()  # Supponiamo che la risposta sia un JSON contenente i punti di raccolta
        
        for point in points:
            folium.Marker(
                location=[point['lat'], point['lon']],
                popup=point['name'],
                icon=folium.Icon(color="blue")
            ).add_to(m)
    else:
        print("Errore nel recupero dei dati.")

import requests
import time
import json

# Function to fetch INGV data with retry and fallback on USGS
def fetch_ingv_data_with_fallback():
    api_url_ingv = "https://webservices.ingv.it/fdsnws/event/1/query?format=geojson"
    api_url_usgs = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"

    retries = 3  # Retry attempts for INGV
    for _ in range(retries):
        try:
            response = requests.get(api_url_ingv)
            response.raise_for_status()  # Check if there are HTTP errors
            return response.json()  # Return data if the request is successful
        except requests.exceptions.RequestException as e:
            print(f"Error with INGV: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying

    # If INGV fails, fallback to USGS
    print("Falling back to USGS data...")
    try:
        response = requests.get(api_url_usgs)
        response.raise_for_status()  # Check if there are HTTP errors
        return response.json()  # Return data from USGS
    except requests.exceptions.RequestException as e:
        print(f"Error with USGS: {e}")
        return None  # Return None if both APIs fail

# Function to cache data
def cache_data(data, cache_file):
    with open(cache_file, 'w') as file:
        json.dump(data, file)

# Function to load data from cache
def load_from_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            return json.load(file)
    return None

# Check if the data is in the cache
cache_file = '/mnt/data/earthquake_cache.json'
data = load_from_cache(cache_file)

if not data:
    print("Data not found in cache, fetching from services...")
    data = fetch_ingv_data_with_fallback()
    if data:
        cache_data(data, cache_file)  # Store the fetched data in cache

# Continue with the use of data
if data:
    print(f"Retrieved {len(data['features'])} seismic events.")
else:
    print("Unable to retrieve data.")
