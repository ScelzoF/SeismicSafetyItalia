
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
    
    "Lazio": {
        "criticita": (
            "Il Lazio presenta un rischio sismico significativo nelle zone interne, in particolare nelle province di Rieti e Frosinone. "
            "Sono presenti anche fenomeni di dissesto idrogeologico, frane e alluvioni in diverse aree collinari e costiere."
        ),
        "punti_raccolta": """
Roma: Piazza del Popolo, Piazza Venezia, Parco della Caffarella
Latina: Piazza del Popolo, Parco Falcone-Borsellino
Frosinone: Piazza della Libertà, Villa Comunale
Rieti: Piazza Vittorio Emanuele II, Parco San Francesco
Viterbo: Piazza del Plebiscito, Parco Prato Giardino
        """,
        "link_utili": {
            "Protezione Civile Lazio": "https://www.regione.lazio.it/protezionecivile",
            "Piani emergenza Lazio": "https://www.regione.lazio.it/protezionecivile/piani-emergenza"
        }
    },

    "Friuli Venezia Giulia": {
        "criticita": (
            "Regione a rischio sismico elevato, con storici eventi importanti (es. terremoto del 1976). "
            "Presenti anche rischi idrogeologici e frane in zona montana."
        ),
        "punti_raccolta": [
            "📍 Trieste – Piazza Unità d'Italia",
            "📍 Udine – Piazza della Libertà",
            "📍 Pordenone – Piazza XX Settembre",
            "📍 Gorizia – Piazza Vittoria"
        ],
        "link_utili": {
            "Protezione Civile FVG": "https://protezionecivile.regione.fvg.it",
            "Piano emergenza regionale": "https://protezionecivile.regione.fvg.it/it/attivita/piani"
        }
    },

    "Trentino-Alto Adige": {
        "criticita": (
            "Zona prevalentemente montana soggetta a frane, valanghe e alluvioni. "
            "Rischio sismico basso ma presente. Elevata attenzione al rischio neve."
        ),
        "punti_raccolta": [
            "📍 Trento – Piazza Duomo",
            "📍 Bolzano – Piazza Walther"
        ],
        "link_utili": {
            "Protezione Civile Trentino": "https://www.protezionecivile.tn.it",
            "Protezione Civile Alto Adige": "https://www.provinz.bz.it/protezione-civile"
        }
    },

    "Umbria": {
        "criticita": (
            "Regione a rischio sismico elevato, in particolare nelle aree di Norcia e Valnerina. "
            "Presenti anche frane e rischio idrogeologico diffuso."
        ),
        "punti_raccolta": [
            "📍 Perugia – Piazza IV Novembre",
            "📍 Terni – Piazza Tacito",
            "📍 Foligno – Piazza della Repubblica"
        ],
        "link_utili": {
            "Protezione Civile Umbria": "https://protezionecivile.regione.umbria.it",
            "Piani di emergenza comunali": "https://protezionecivile.regione.umbria.it/piani-di-emergenza"
        }
    },

    "Valle d'Aosta": {
        "criticita": (
            "Zona montana soggetta a valanghe, frane e rischio idrogeologico. "
            "Rischio sismico basso ma monitorato nelle valli."
        ),
        "punti_raccolta": [
            "📍 Aosta – Piazza Chanoux"
        ],
        "link_utili": {
            "Protezione Civile Valle d'Aosta": "https://www.regione.vda.it/protezione_civile"
        }
    },

    "Sardegna": {
        "criticita": (
            "Rischio idrogeologico localizzato, soprattutto nelle aree del nuorese e del cagliaritano. "
            "Rischio sismico molto basso, ma presenti incendi boschivi estivi."
        ),
        "punti_raccolta": [
            "📍 Cagliari – Piazza Yenne",
            "📍 Sassari – Piazza d'Italia",
            "📍 Nuoro – Piazza Vittorio Emanuele",
            "📍 Oristano – Piazza Eleonora d'Arborea"
        ],
        "link_utili": {
            "Protezione Civile Sardegna": "https://www.sardegnaambiente.it/protezionecivile",
            "Piani emergenza comunali": "https://www.sardegnaambiente.it/index.php?xsl=612&s=408130&v=2&c=5264&idsito=19"
        }
    },

    "Liguria": {
        "criticita": (
            "La Liguria è fortemente esposta a rischio idrogeologico, con frane e alluvioni frequenti specialmente nelle aree costiere e montane. "
            "Il territorio presenta una vulnerabilità sismica bassa, ma significativa in alcune zone."
        ),
        "punti_raccolta": [
            "📍 Genova – Piazza De Ferrari",
            "📍 La Spezia – Piazza Europa",
            "📍 Savona – Piazza Mameli",
            "📍 Imperia – Piazza Dante"
        ],
        "link_utili": {
            "Protezione Civile Liguria": "https://www.allertaliguria.gov.it",
            "Piano emergenza Liguria": "https://www.regione.liguria.it/protezione-civile"
        }
    },

    "Marche": {
        "criticita": (
            "Le Marche presentano un rischio sismico elevato, soprattutto nelle province interne. "
            "È presente anche un rischio idrogeologico lungo le valli fluviali e in aree collinari."
        ),
        "punti_raccolta": [
            "📍 Ancona – Piazza Roma",
            "📍 Pesaro – Piazza del Popolo",
            "📍 Macerata – Piazza della Libertà",
            "📍 Ascoli Piceno – Piazza del Popolo",
            "📍 Fermo – Piazza del Popolo"
        ],
        "link_utili": {
            "Protezione Civile Marche": "https://protezionecivile.regione.marche.it",
            "Piani emergenza comunali": "https://protezionecivile.regione.marche.it/strumenti/piani-di-emergenza"
        }
    },

    "Piemonte": {
        "criticita": (
            "Il Piemonte è soggetto a rischio idrogeologico, con frane e alluvioni concentrate nelle valli alpine. "
            "È presente anche un rischio sismico moderato in alcune zone del sud della regione."
        ),
        "punti_raccolta": [
            "📍 Torino – Piazza Castello",
            "📍 Novara – Piazza Martiri della Libertà",
            "📍 Alessandria – Piazza della Libertà",
            "📍 Cuneo – Piazza Galimberti",
            "📍 Asti – Piazza San Secondo"
        ],
        "link_utili": {
            "Protezione Civile Piemonte": "https://www.regione.piemonte.it/web/temi/protezione-civile",
            "Piani di emergenza comunali": "https://www.protezionecivilepiemonte.it"
        }
    },

    "Lombardia": {
        "criticita": (
            "La Lombardia è esposta a rischio idrogeologico, con frane e alluvioni frequenti nelle zone alpine e prealpine. "
            "Alcune aree presentano vulnerabilità sismica moderata."
        ),
        "punti_raccolta": [
            "📍 Milano – Parco Sempione",
            "📍 Bergamo – Piazza Matteotti",
            "📍 Brescia – Piazza della Loggia",
            "📍 Como – Piazza Cavour",
            "📍 Varese – Giardini Estensi"
        ],
        "link_utili": {
            "Protezione Civile Lombardia": "https://www.protezionecivile.regione.lombardia.it",
            "Piani di emergenza locali": "https://www.protezionecivile.regione.lombardia.it/wps/portal/site/pcrl/prevenzione/piani-emergenza"
        }
    },

    "Toscana": {
        "criticita": (
            "La Toscana è soggetta a rischio idrogeologico e sismico, con eventi significativi registrati in passato nella zona del Mugello e in Garfagnana. "
            "Frane e alluvioni interessano frequentemente le zone appenniniche."
        ),
        "punti_raccolta": [
            "📍 Firenze – Piazza Santa Maria Novella",
            "📍 Pisa – Piazza dei Miracoli",
            "📍 Arezzo – Piazza Grande",
            "📍 Lucca – Piazza Napoleone",
            "📍 Grosseto – Piazza Dante"
        ],
        "link_utili": {
            "Protezione Civile Toscana": "https://www.regione.toscana.it/protezionecivile",
            "Piani di emergenza comunali": "https://www.regione.toscana.it/-/piani-di-protezione-civile-comunali"
        }
    },

    "Veneto": {
        "criticita": (
            "Il Veneto presenta rischio idrogeologico elevato, con frequenti frane e alluvioni, specialmente in montagna e nelle aree fluviali. "
            "È presente anche un rischio sismico moderato nelle zone pedemontane."
        ),
        "punti_raccolta": [
            "📍 Venezia – Piazzale Roma",
            "📍 Verona – Piazza Bra",
            "📍 Padova – Prato della Valle",
            "📍 Treviso – Piazza dei Signori",
            "📍 Vicenza – Piazza dei Signori"
        ],
        "link_utili": {
            "Protezione Civile Veneto": "https://www.protezionecivileveneto.it",
            "Piano emergenza regionale": "https://www.protezionecivileveneto.it/piani-emergenza"
        }
    },

    
    
    "Basilicata": {
        "criticita": (
            "La Basilicata è esposta a rischio sismico, in particolare nelle aree di Potenza e Melfi. "
            "Sono presenti anche fenomeni di dissesto idrogeologico e frane nelle zone montane."
        ),
        "punti_raccolta": """
Potenza: Piazza Mario Pagano, Parco Montereale
Matera: Piazza Vittorio Veneto, Parco Giovanni Paolo II
Melfi: Piazza Umberto I, Parco Comunale
Policoro: Piazza Eraclea, Centro sportivo comunale
        """,
        "link_utili": {
            "Protezione Civile Basilicata": "https://protezionecivile.regione.basilicata.it",
            "Piano di emergenza Basilicata": "https://protezionecivile.regione.basilicata.it/piani-emergenza"
        }
    },

    "Molise": {
        "criticita": (
            "Il Molise presenta un rischio sismico elevato, soprattutto nelle province di Campobasso e Isernia. "
            "Sono presenti anche aree soggette a frane e dissesto idrogeologico."
        ),
        "punti_raccolta": [
            "📍 Campobasso – Piazza Vittorio Emanuele II",
            "📍 Isernia – Piazza Andrea d'Isernia",
            "📍 Termoli – Piazza Vittorio Veneto"
        ],
        "link_utili": {
            "Protezione Civile Molise": "https://www.protezionecivile.molise.it",
            "Piano di emergenza Molise": "https://www.protezionecivile.molise.it/piano-emergenza"
        }
    },

    "Sicilia": {
        "criticita": (
            "La Sicilia è una delle regioni a più alto rischio sismico e vulcanico in Italia. "
            "Le aree maggiormente esposte includono la zona dell'Etna, le Isole Eolie e la Sicilia orientale. "
            "Sono presenti anche rischi idrogeologici, frane e incendi boschivi durante l'estate."
        ),
        "punti_raccolta": [
            "📍 Palermo – Piazza Castelnuovo",
            "📍 Catania – Piazza Università",
            "📍 Messina – Piazza Cairoli",
            "📍 Siracusa – Parco Archeologico della Neapolis",
            "📍 Agrigento – Piazzale Aldo Moro",
            "📍 Trapani – Piazza Vittorio Veneto",
            "📍 Ragusa – Piazza San Giovanni",
            "📍 Enna – Piazza Europa",
            "📍 Caltanissetta – Villa Cordova"
        ],
        "link_utili": {
            "Protezione Civile Sicilia": "https://www.protezionecivilesicilia.it",
            "Piano regionale di emergenza": "https://www.protezionecivilesicilia.it/piano-emergenza"
        }
    },

    "Puglia": {
        "criticita": (
            "La Puglia presenta un rischio sismico moderato, in particolare nel Gargano e nella zona della Murgia. "
            "È esposta anche a fenomeni di dissesto idrogeologico, alluvioni improvvise e incendi boschivi nelle aree rurali."
        ),
        "punti_raccolta": [
            "📍 Bari – Piazza Libertà",
            "📍 Foggia – Piazza Cavour",
            "📍 Lecce – Parco Belloluogo",
            "📍 Taranto – Villa Peripato",
            "📍 Brindisi – Piazza Vittoria",
            "📍 Barletta – Piazza Aldo Moro"
        ],
        "link_utili": {
            "Protezione Civile Puglia": "http://www.protezionecivile.puglia.it",
            "Piano di emergenza regionale": "http://www.protezionecivile.puglia.it/piani-di-emergenza"
        }
    },

    
        
    "Campania": {
        "criticita": (
            "Regione ad alto rischio sismico e vulcanico, in particolare nelle aree del Vesuvio e dei Campi Flegrei. "
            "Sono presenti anche fenomeni di dissesto idrogeologico."
        ),
        "punti_raccolta": """
Napoli: Piazza del Plebiscito, Mostra d'Oltremare
Salerno: Piazza della Concordia, Parco Pinocchio
Avellino: Piazza Libertà, Villa Comunale
Benevento: Piazza Risorgimento, Parco Cellarulo
Caserta: Piazza Vanvitelli, Reggia di Caserta
        """,
        "link_utili": {
            "Protezione Civile Campania": "http://www.protezionecivile.regione.campania.it",
            "Piano di emergenza Vesuvio": "http://www.protezionecivile.gov.it/vesuvio"
        }
    },
                
    "Abruzzo": {
        "criticita": "Rischio sismico elevato, frane e alluvioni frequenti.",
        "punti_raccolta": """L'Aquila: Piazza Duomo, Parco del Castello
Teramo: Piazza Martiri, Stadio Comunale
Pescara: Parco Villa Sabucchi, Piazza della Repubblica
Chieti: Piazza San Giustino, Parco Archeologico La Civitella""",
        "link_utili": {
            "Protezione Civile Abruzzo": "https://protezionecivile.regione.abruzzo.it",
            "ARPA Abruzzo": "https://www.arpaabruzzo.it"
        }
    },
                
                                        
    
    "Calabria": {
        "criticita": (
            "Rischio sismico elevato in tutta la regione, in particolare nella zona di Reggio Calabria. "
            "Frane e incendi boschivi frequenti durante l'estate."
        ),
        "punti_raccolta": """
Catanzaro: Piazza Prefettura, Parco della Biodiversità
Reggio Calabria: Piazza Italia, Lungomare Falcomatà
Cosenza: Piazza dei Bruzi, Villa Vecchia
Crotone: Piazza Pitagora, Parco Pignera
Vibo Valentia: Piazza Municipio, Parco Urbano
        """,
        "link_utili": {
            "Protezione Civile Calabria": "https://www.protezionecivilecalabria.it",
            "Piani emergenza Calabria": "https://www.protezionecivilecalabria.it/piani-emergenza"
        }
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
        st.markdown(f"""```\n{dati_regioni[regione_sel]["punti_raccolta"]}\n```""")
        st.markdown("### 🔗 Link utili")
        st.markdown(dati_regioni[regione_sel]["link_utili"])


    # ================== EVENTI: COSA FARE / NON FARE ==================

    st.markdown("---")
    st.subheader("⚠️ Cosa fare e non fare in base all'evento")

    evento = st.selectbox("Scegli l'evento", [
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
        st.subheader("🔥 Cosa fare in caso di INCENDIO")
        st.markdown("- Allontanarsi immediatamente dalla zona dell’incendio")
        st.markdown("- Coprire naso e bocca con un panno umido")
        st.markdown("- Segnalare l’incendio al 115")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non tentare di spegnere incendi estesi da soli")
        st.markdown("- Non intralciare le vie di fuga")
    elif evento == "Frana":
        st.subheader("⛰️ Cosa fare in caso di FRANA")
        st.markdown("- Allontanarsi velocemente dalla zona a rischio")
        st.markdown("- Seguire i percorsi di evacuazione indicati")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non sostare sotto pendii o versanti instabili")
    elif evento == "Neve":
        st.subheader("❄️ Cosa fare in caso di NEVE intensa")
        st.markdown("- Evitare spostamenti non necessari")
        st.markdown("- Tenere in auto catene da neve o pneumatici invernali")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non utilizzare mezzi non adeguati")
    elif evento == "Tempesta":
        st.subheader("🌪️ Cosa fare in caso di TEMPESTA")
        st.markdown("- Restare in casa, lontani da finestre")
        st.markdown("- Spegnere apparecchi elettrici non necessari")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non uscire se non strettamente necessario")
    elif evento == "Emergenza sanitaria":
        st.subheader("🧪 Cosa fare in caso di EMERGENZA SANITARIA")
        st.markdown("- Seguire le indicazioni delle autorità sanitarie")
        st.markdown("- Indossare DPI se richiesto")
        st.markdown("- Evitare assembramenti")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non diffondere dati reali da fonte ufficiale news")
    elif evento == "Blackout":
        st.subheader("⚫ Cosa fare in caso di BLACKOUT")
        st.markdown("- Usare torce a batteria")
        st.markdown("- Staccare gli elettrodomestici per evitare sbalzi")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non usare candele vicino a materiali infiammabili")
    elif evento == "Emergenza nucleare":
        st.subheader("☢️ Cosa fare in caso di EMERGENZA NUCLEARE")
        st.markdown("- Chiudersi in casa sigillando porte e finestre")
        st.markdown("- Seguire le indicazioni delle autorità")
        st.markdown("- Sintonizzarsi su canali ufficiali")
        st.markdown("#### ❌ Cosa NON fare")
        st.markdown("- Non uscire per curiosare")
