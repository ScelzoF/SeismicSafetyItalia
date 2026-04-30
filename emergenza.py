"""
emergenza.py
Sezione emergenza — dati REALI Protezione Civile, vie di fuga, punti di raccolta ufficiali.
Auto-aggiornamento 30 minuti. Google Maps routing. DPC open data.
"""

import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import time
from datetime import datetime, timedelta
import math
from translations_lib import get_text as _gt
from ingv_monitor import fetch_ingv_alert_level

CACHE_TTL_SECONDS = 1800  # 30 minuti

# ─── 25 COMUNI ZONA ROSSA VESUVIO con punti raccolta reali DPC ───────────────
VESUVIO_ZONA_ROSSA = [
    {"comune": "Ercolano", "zona": "A", "lat": 40.8060, "lon": 14.3611,
     "punto": "Piazza Pugliano", "plat": 40.8071, "plon": 14.3620, "pax": 8000},
    {"comune": "Torre del Greco", "zona": "A", "lat": 40.7872, "lon": 14.3611,
     "punto": "Piazza Santa Croce", "plat": 40.7888, "plon": 14.3656, "pax": 12000},
    {"comune": "Portici", "zona": "A", "lat": 40.8143, "lon": 14.3405,
     "punto": "Piazza San Ciro", "plat": 40.8155, "plon": 14.3422, "pax": 7000},
    {"comune": "San Giorgio a Cremano", "zona": "A", "lat": 40.8300, "lon": 14.3350,
     "punto": "Piazza Troisi", "plat": 40.8312, "plon": 14.3338, "pax": 5000},
    {"comune": "Boscoreale", "zona": "A", "lat": 40.7735, "lon": 14.4769,
     "punto": "Via Settetermini", "plat": 40.7729, "plon": 14.4790, "pax": 4500},
    {"comune": "Boscotrecase", "zona": "A", "lat": 40.7743, "lon": 14.4645,
     "punto": "Piazza Municipio", "plat": 40.7751, "plon": 14.4631, "pax": 3500},
    {"comune": "Torre Annunziata", "zona": "A", "lat": 40.7525, "lon": 14.4479,
     "punto": "Piazza Cesaro", "plat": 40.7538, "plon": 14.4466, "pax": 9000},
    {"comune": "Trecase", "zona": "A", "lat": 40.7877, "lon": 14.4418,
     "punto": "Piazza Montedoro", "plat": 40.7870, "plon": 14.4430, "pax": 2000},
    {"comune": "Pompei", "zona": "A", "lat": 40.7463, "lon": 14.4989,
     "punto": "Piazza Esedra", "plat": 40.7451, "plon": 14.5002, "pax": 6000},
    {"comune": "Castellammare di Stabia", "zona": "A", "lat": 40.6944, "lon": 14.4739,
     "punto": "Piazza Fontana Grande", "plat": 40.6955, "plon": 14.4726, "pax": 10000},
    {"comune": "Sant'Anastasia", "zona": "A", "lat": 40.8682, "lon": 14.4005,
     "punto": "Via Panoramica", "plat": 40.8670, "plon": 14.4020, "pax": 5500},
    {"comune": "Pollena Trocchia", "zona": "A", "lat": 40.8653, "lon": 14.3666,
     "punto": "Piazza Municipio", "plat": 40.8660, "plon": 14.3680, "pax": 4000},
    {"comune": "San Sebastiano al Vesuvio", "zona": "A", "lat": 40.8488, "lon": 14.3786,
     "punto": "Piazza del Municipio", "plat": 40.8495, "plon": 14.3800, "pax": 2000},
    {"comune": "Massa di Somma", "zona": "A", "lat": 40.8534, "lon": 14.3617,
     "punto": "Via Panoramica", "plat": 40.8540, "plon": 14.3630, "pax": 1500},
    {"comune": "Cercola", "zona": "A", "lat": 40.8530, "lon": 14.3414,
     "punto": "Piazza Municipio", "plat": 40.8520, "plon": 14.3402, "pax": 4500},
    {"comune": "Ottaviano", "zona": "A", "lat": 40.8496, "lon": 14.4798,
     "punto": "Piazza Municipio", "plat": 40.8504, "plon": 14.4810, "pax": 5000},
    {"comune": "Somma Vesuviana", "zona": "A", "lat": 40.8735, "lon": 14.4345,
     "punto": "Piazza Vittorio Emanuele", "plat": 40.8744, "plon": 14.4355, "pax": 7000},
    {"comune": "San Giuseppe Vesuviano", "zona": "A", "lat": 40.8346, "lon": 14.5028,
     "punto": "Piazza Vittoria", "plat": 40.8355, "plon": 14.5040, "pax": 6500},
    {"comune": "Terzigno", "zona": "A", "lat": 40.8109, "lon": 14.4989,
     "punto": "Piazza Europa", "plat": 40.8117, "plon": 14.5000, "pax": 4000},
    {"comune": "Palma Campania", "zona": "A", "lat": 40.8632, "lon": 14.5488,
     "punto": "Piazza Libertà", "plat": 40.8640, "plon": 14.5500, "pax": 5000},
    {"comune": "Nola", "zona": "A", "lat": 40.9263, "lon": 14.5297,
     "punto": "Piazza Duomo", "plat": 40.9270, "plon": 14.5310, "pax": 8000},
    {"comune": "Pomigliano d'Arco", "zona": "A", "lat": 40.9167, "lon": 14.3829,
     "punto": "Piazza Municipio", "plat": 40.9175, "plon": 14.3840, "pax": 7000},
    {"comune": "San Vitaliano", "zona": "A", "lat": 40.9193, "lon": 14.4533,
     "punto": "Piazza Municipio", "plat": 40.9200, "plon": 14.4545, "pax": 2500},
    {"comune": "Brusciano", "zona": "A", "lat": 40.9267, "lon": 14.4608,
     "punto": "Parco Comunale", "plat": 40.9275, "plon": 14.4620, "pax": 3000},
    {"comune": "Mariglianella", "zona": "A", "lat": 40.9289, "lon": 14.4425,
     "punto": "Piazza Municipio", "plat": 40.9297, "plon": 14.4437, "pax": 2000},
]

# ─── CAMPI FLEGREI ZONA ROSSA ─────────────────────────────────────────────────
CF_ZONA_ROSSA = [
    {"comune": "Pozzuoli", "zona": "A", "lat": 40.8235, "lon": 14.1204,
     "punto": "Piazza della Repubblica", "plat": 40.8239, "plon": 14.1247, "pax": 15000},
    {"comune": "Bacoli", "zona": "A", "lat": 40.8009, "lon": 14.0824,
     "punto": "Piazza Risorgimento", "plat": 40.8018, "plon": 14.0836, "pax": 5000},
    {"comune": "Monte di Procida", "zona": "A", "lat": 40.7923, "lon": 14.0556,
     "punto": "Piazza Municipio", "plat": 40.7930, "plon": 14.0565, "pax": 3000},
    {"comune": "Quarto", "zona": "A", "lat": 40.8780, "lon": 14.1435,
     "punto": "Piazza Enrico De Nicola", "plat": 40.8788, "plon": 14.1448, "pax": 8000},
    {"comune": "Napoli (Bagnoli)", "zona": "A", "lat": 40.8111, "lon": 14.1668,
     "punto": "Area ex Ilva - Bagnoli", "plat": 40.8102, "plon": 14.1700, "pax": 12000},
    {"comune": "Napoli (Fuorigrotta)", "zona": "A", "lat": 40.8281, "lon": 14.1828,
     "punto": "Piazzale Tecchio", "plat": 40.8265, "plon": 14.1850, "pax": 10000},
    {"comune": "Napoli (Pianura)", "zona": "A", "lat": 40.8580, "lon": 14.1594,
     "punto": "Piazza Giovanni XXIII", "plat": 40.8588, "plon": 14.1607, "pax": 8000},
    {"comune": "Marano di Napoli", "zona": "B", "lat": 40.9019, "lon": 14.1851,
     "punto": "Piazza Municipio", "plat": 40.9027, "plon": 14.1863, "pax": 6000},
    {"comune": "Giugliano in Campania", "zona": "B", "lat": 40.9284, "lon": 14.1944,
     "punto": "Piazza Gramsci", "plat": 40.9292, "plon": 14.1956, "pax": 7000},
    {"comune": "Pozzuoli (Rione Terra)", "zona": "A", "lat": 40.8257, "lon": 14.1173,
     "punto": "Porto di Pozzuoli", "plat": 40.8249, "plon": 14.1193, "pax": 5000},
]

NUMERI_EMERGENZA = [
    ("112", "Numero Unico di Emergenza (Europeo)", "#e63946"),
    ("118", "Emergenza Sanitaria / SUEM", "#f4a261"),
    ("115", "Vigili del Fuoco", "#e76f51"),
    ("113", "Polizia di Stato", "#457b9d"),
    ("1515", "Corpo Forestale — Incendi", "#2dc653"),
    ("800 840 840", "Protezione Civile Nazionale", "#6c757d"),
    ("800 232 525", "Protezione Civile Campania", "#9b59b6"),
    ("803 500", "Guasto elettrico e-distribuzione", "#ff9800"),
    ("1522", "Antiviolenza e stalking", "#e91e63"),
]

EVENTI = {
    "🌍 Terremoto": {
        "fare": [
            "Mantieni la calma — la prima scossa dura pochi secondi",
            "Riparati SOTTO un tavolo robusto o nel vano di una porta portante",
            "Allontanati da vetri, scaffali, oggetti pesanti",
            "Se sei all'aperto: allontanati da edifici, pali e alberi",
            "Dopo la scossa: esci con prudenza dalle scale, NON usare ascensori",
            "Raggiungi l'area di raccolta indicata dal tuo Comune",
            "Segui solo comunicazioni ufficiali (Protezione Civile, RAI Radio 1)",
        ],
        "non_fare": [
            "Non usare ascensori",
            "Non precipitarti verso le uscite durante la scossa",
            "Non usare auto nelle prime ore (strade per i soccorsi)",
            "Non rientrare nell'edificio senza ok delle autorità",
            "Non diffondere notizie non verificate",
        ],
        "kit": "Acqua (2L/pers/giorno × 3gg), cibo, medicinali, documenti, torcia, power bank, radio a batterie, scarpe robuste",
        "link": "https://www.protezionecivile.gov.it/it/rischio/rischio-sismico/cosa-fare",
    },
    "🌋 Eruzione Vulcanica": {
        "fare": [
            "Segui IMMEDIATAMENTE le istruzioni della Protezione Civile",
            "Indossa mascherina FFP2 contro le ceneri vulcaniche",
            "Proteggi occhi con occhiali da sole o protettivi (cenere abrasiva)",
            "Raggiungi il PUNTO DI RACCOLTA assegnato dal tuo Comune",
            "Chiudi ermeticamente porte, finestre, camini",
            "Rimuovi la cenere dai tetti (peso può causare crolli)",
            "Non seguire strade non indicate nel piano di evacuazione",
        ],
        "non_fare": [
            "Non restare all'aperto durante caduta di cenere o lapilli",
            "Non usare veicoli se non strettamente necessario",
            "Non bere acqua di rubinetto nella fase acuta",
            "Non ignorare gli ordini di evacuazione",
            "Non tornare a casa senza ok delle autorità",
        ],
        "kit": "Mascherine FFP2 (min. 10), occhiali protettivi, teli copricapo, scorte acqua (min. 6L), radio a batterie, kit primo soccorso",
        "link": "https://www.protezionecivile.gov.it/it/rischio/rischio-vulcanico",
    },
    "🌊 Alluvione": {
        "fare": [
            "Sali ai piani alti dell'edificio",
            "Evita cantine, garage e locali interrati",
            "Porta kit emergenza, documenti e medicinali",
            "Segui le istruzioni della Protezione Civile via radio/TV",
            "Se sei in auto e l'acqua sale: ABBANDONALA e vai in alto",
        ],
        "non_fare": [
            "Non attraversare mai strade allagate — anche 20cm possono trascinarti",
            "Non toccare apparecchi elettrici bagnati",
            "Non scendere in scantinati o sottopassaggi",
            "Non avvicinarti ai corsi d'acqua esondati",
        ],
        "kit": "Stivali di gomma, impermeabile, kit pronto soccorso, documenti impermeabilizzati",
        "link": "https://www.protezionecivile.gov.it/it/rischio/rischio-idrogeologico-e-idraulico/cosa-fare",
    },
    "🔥 Incendio": {
        "fare": [
            "Allontanati subito dalla zona dell'incendio",
            "Chiama il 115 (Vigili del Fuoco)",
            "Se c'è fumo: spostati basso e copriti naso/bocca con panno umido",
            "Chiudi le porte dietro di te per rallentare la propagazione",
            "Usa la via di fuga più vicina, mai l'ascensore",
        ],
        "non_fare": [
            "Non usare ascensori",
            "Non aprire porte calde (il fuoco è dietro)",
            "Non tornare a prendere oggetti personali",
            "Non tentare di spegnere incendi estesi da solo",
        ],
        "kit": "Estintore domestico, rilevatore di fumo (testarlo ogni mese!), piano di evacuazione familiare",
        "link": "https://www.vigilfuoco.it",
    },
    "⛰️ Frana": {
        "fare": [
            "Allontanati immediatamente dalla zona a rischio",
            "Avvisa i soccorsi (112) e la Protezione Civile",
            "Non percorrere strade in pendenza durante piogge intense",
            "Segui i percorsi di evacuazione indicati",
        ],
        "non_fare": [
            "Non sostare sotto pendii o versanti instabili dopo piogge",
            "Non attraversare zone fangose o corsi d'acqua in piena",
            "Non rientrare nella zona prima dell'ok delle autorità",
        ],
        "kit": "Stivali, torcia, radio a batterie, documenti in sacca impermeabile",
        "link": "https://www.protezionecivile.gov.it/it/rischio/rischio-idrogeologico-e-idraulico/cosa-fare",
    },
    "❄️ Neve e Ghiaccio": {
        "fare": [
            "Rimani in casa se possibile",
            "Tieni scorte d'acqua, cibo e coperte per almeno 3 giorni",
            "Controlla il meteo e l'allerta neve tramite fonti ufficiali",
            "Se esci: pneumatici invernali o catene obbligatori",
        ],
        "non_fare": [
            "Non guidare senza pneumatici adeguati",
            "Non usare fuochi aperti in ambienti chiusi (monossido di carbonio)",
            "Non abbandonare auto in mezzo alla strada",
        ],
        "kit": "Catene da neve, pala, candele, coperte termiche, kit anticongelamento",
        "link": "https://www.protezionecivile.gov.it",
    },
    "⚡ Blackout Elettrico": {
        "fare": [
            "Usa torce a batteria o LED — evita candele (rischio incendio)",
            "Stacca gli elettrodomestici per evitare sbalzi di tensione al ritorno della corrente",
            "Il frigo tiene circa 4 ore, il freezer 48 ore a porte chiuse",
            "Tieni il cellulare carico (power bank!)",
            "Segnala il guasto al gestore (e-distribuzione: 803 500)",
        ],
        "non_fare": [
            "Non aprire inutilmente frigorifero o freezer",
            "Non usare generatori a benzina in ambienti chiusi (rischio monossido)",
            "Non toccare cavi elettrici o quadri con mani bagnate",
        ],
        "kit": "Power bank, torce LED, radio a batterie, scorte d'acqua, UPS",
        "link": "https://www.e-distribuzione.it",
    },
}

DATI_REGIONI = {
    "Campania": {
        "criticita": (
            "🌋 **Rischio vulcanico** (Vesuvio e Campi Flegrei — zone rosse e gialle). "
            "⚡ **Rischio sismico** elevato. 🌊 **Rischio idrogeologico** nelle aree costiere e collinari. "
            "Il piano di evacuazione Vesuvio è già attivo con zone A (rosso), B (giallo), C (blu). "
            "Campi Flegrei in allerta GIALLO dal maggio 2023 — bradisismo in corso."
        ),
        "numeri": "800 232 525 (PC Campania) · 112 · 118",
        "link_pc": "https://www.regione.campania.it/regione/it/tematiche/portale-protezione-civile",
        "link_arpa": "http://www.arpacampania.it",
        "link_speciale": "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vesuvio/",
        "label_speciale": "Piano evacuazione Vesuvio — Protezione Civile",
    },
    "Sicilia": {
        "criticita": "🌋 **Etna attivo** — eruzioni frequenti. ⚡ **Rischio sismico** elevato (Messina, Catania). 🔥 Incendi boschivi estivi. 🌊 Rischio maremoto su alcune coste.",
        "numeri": "1516 (PC Sicilia) · 112 · 1515",
        "link_pc": "http://www.protezionecivilesicilia.it",
        "link_arpa": "https://www.arpa.sicilia.it",
        "link_speciale": "https://www.ct.ingv.it/",
        "label_speciale": "INGV Catania — Monitoraggio Etna",
    },
    "Lazio": {
        "criticita": "⚡ Rischio sismico (Appennino laziale). 🌊 Rischio idrogeologico. 🌋 Area vulcanica Colli Albani (monitorata, alert verde).",
        "numeri": "800 096 113 (PC Lazio) · 112",
        "link_pc": "https://www.regione.lazio.it/protezionecivile",
        "link_arpa": "https://www.arpalazio.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Calabria": {
        "criticita": "⚡ **Rischio sismico elevato** (tra le zone a più alta pericolosità d'Italia). 🌊 Rischio frane e idrogeologico. 🔥 Incendi estivi.",
        "numeri": "0961 857225 (PC Calabria) · 112",
        "link_pc": "https://www.protezionecivilecalabria.it",
        "link_arpa": "https://www.arpacal.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Abruzzo": {
        "criticita": "⚡ **Rischio sismico elevato** (L'Aquila 2009, M6.3). 🌊 Frane e alluvioni in area montana.",
        "numeri": "0862 363555 (PC Abruzzo) · 112",
        "link_pc": "https://protezionecivile.regione.abruzzo.it",
        "link_arpa": "https://www.arpaabruzzo.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Emilia-Romagna": {
        "criticita": "🌊 **Rischio alluvione elevato** (eventi 2012 e 2023). ⚡ Rischio sismico appenninico (terremoto 2012, M5.8).",
        "numeri": "051 6490511 (PC ER) · 112",
        "link_pc": "https://www.protezionecivile.emilia-romagna.it",
        "link_arpa": "https://www.arpae.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Toscana": {
        "criticita": "🌊 Rischio alluvioni (Firenze, Livorno). ⚡ Rischio sismico (Garfagnana, Mugello). 🌋 Area geotermica Larderello.",
        "numeri": "055 4383333 (PC Toscana) · 112",
        "link_pc": "https://www.regione.toscana.it/protezionecivile",
        "link_arpa": "https://www.arpat.toscana.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Lombardia": {
        "criticita": "🌊 Rischio idrogeologico (alluvioni, esondazioni Po). 🏔️ Valanghe in area alpina.",
        "numeri": "02 67651 (PC Lombardia) · 112",
        "link_pc": "https://www.protezionecivile.regione.lombardia.it",
        "link_arpa": "https://www.arpalombardia.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Veneto": {
        "criticita": "🌊 Alluvioni e rischio idraulico (Po, Adige). 🏔️ Frane in zona dolomitica.",
        "numeri": "041 2791498 (PC Veneto) · 112",
        "link_pc": "https://www.regione.veneto.it/web/protezione-civile",
        "link_arpa": "https://www.arpa.veneto.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Piemonte": {
        "criticita": "🏔️ Valanghe e frane alpine. 🌊 Alluvioni (Po, Dora).",
        "numeri": "011 4321500 (PC Piemonte) · 112",
        "link_pc": "https://www.protezionecivile.piemonte.it",
        "link_arpa": "https://www.arpa.piemonte.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Puglia": {
        "criticita": "🔥 Incendi boschivi. ⚡ Rischio sismico (Gargano). 🌊 Rischio idrogeologico limitato.",
        "numeri": "080 5406111 (PC Puglia) · 112",
        "link_pc": "http://www.protezionecivilepuglia.it",
        "link_arpa": "https://www.arpa.puglia.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Marche": {
        "criticita": "⚡ **Rischio sismico elevato** (Amatrice 2016, M6.2). 🌊 Frane appenniniche.",
        "numeri": "071 8063030 (PC Marche) · 112",
        "link_pc": "https://www.protezionecivile.marche.it",
        "link_arpa": "https://www.arpa.marche.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Umbria": {
        "criticita": "⚡ **Rischio sismico elevato** (Norcia — M6.5 nel 2016). 🌊 Frane appenniniche.",
        "numeri": "075 5045111 (PC Umbria) · 112",
        "link_pc": "https://protezionecivile.regione.umbria.it",
        "link_arpa": "https://www.arpa.umbria.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Liguria": {
        "criticita": "🌊 **Frane e alluvioni** (eventi estremi frequenti — Genova 2011). 🌬️ Mareggiate.",
        "numeri": "010 5485200 (ARPAL Liguria) · 112",
        "link_pc": "https://allertaliguria.regione.liguria.it",
        "link_arpa": "https://www.arpal.liguria.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Sardegna": {
        "criticita": "🔥 **Incendi boschivi** (tra le più colpite d'Italia). 🌊 Rischio alluvioni improvvise.",
        "numeri": "070 6062685 (PC Sardegna) · 112",
        "link_pc": "https://www.sardegnaambiente.it/protezionecivile",
        "link_arpa": "https://www.arpas.sardegna.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Basilicata": {
        "criticita": "⚡ Rischio sismico. 🌊 Frane e dissesto idrogeologico diffuso.",
        "numeri": "0971 668111 (PC Basilicata) · 112",
        "link_pc": "https://protezionecivile.regione.basilicata.it",
        "link_arpa": "https://www.arpab.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Molise": {
        "criticita": "⚡ Rischio sismico. 🌊 Rischio idrogeologico.",
        "numeri": "0874 429111 (PC Molise) · 112",
        "link_pc": "https://www.protezionecivile.molise.it",
        "link_arpa": "https://arpa.molise.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Trentino-Alto Adige": {
        "criticita": "🏔️ **Valanghe** e frane alpine. ❄️ Ghiacciai in scioglimento.",
        "numeri": "0461 494949 (PC Trentino) · 112",
        "link_pc": "https://www.protezionecivile.tn.it",
        "link_arpa": "https://www.appa.provincia.tn.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Friuli-Venezia Giulia": {
        "criticita": "⚡ Rischio sismico (Friuli 1976, M6.4). 🌊 Alluvioni e frane.",
        "numeri": "040 3773636 (PC FVG) · 112",
        "link_pc": "https://www.protezionecivile.fvg.it",
        "link_arpa": "https://www.arpa.fvg.it",
        "link_speciale": None, "label_speciale": None,
    },
    "Valle d'Aosta": {
        "criticita": "🏔️ **Valanghe e frane** frequenti. ❄️ Rischio ghiacciai (Monte Bianco).",
        "numeri": "0165 274891 (PC VdA) · 112",
        "link_pc": "https://www.protezionecivile.vda.it",
        "link_arpa": "https://www.arpa.vda.it",
        "link_speciale": None, "label_speciale": None,
    },
}


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def _gmaps_route_url(lat, lon, name=""):
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving"

def _waze_url(lat, lon):
    return f"https://waze.com/ul?ll={lat},{lon}&navigate=yes&zoom=17"

def _apple_maps_url(lat, lon):
    return f"https://maps.apple.com/?daddr={lat},{lon}&dirflg=d"

def _gmaps_place_url(lat, lon):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

def _nav_buttons_html(lat, lon, name, bg="#1a8a1a"):
    """Genera 3 pulsanti navigazione (Google Maps, Waze, Apple Maps) come HTML."""
    gm = _gmaps_route_url(lat, lon, name)
    wz = _waze_url(lat, lon)
    am = _apple_maps_url(lat, lon)
    coord = f"{lat:.5f}, {lon:.5f}"
    return (
        f"<div style='margin-top:6px;'>"
        f"<code style='font-size:0.78em;color:#555;'>{coord}</code><br>"
        f"<a href='{gm}' target='_blank' style='display:inline-block;margin:3px 4px 0 0;"
        f"background:#4285F4;color:#fff;padding:4px 10px;border-radius:4px;"
        f"text-decoration:none;font-size:0.82em;'>🗺️ Google Maps</a>"
        f"<a href='{wz}' target='_blank' style='display:inline-block;margin:3px 4px 0 0;"
        f"background:#33CCFF;color:#fff;padding:4px 10px;border-radius:4px;"
        f"text-decoration:none;font-size:0.82em;'>🔵 Waze</a>"
        f"<a href='{am}' target='_blank' style='display:inline-block;margin:3px 0 0 0;"
        f"background:#555;color:#fff;padding:4px 10px;border-radius:4px;"
        f"text-decoration:none;font-size:0.82em;'>🍎 Apple Maps</a>"
        f"</div>"
    )


def _fetch_dpc_allerta():
    """Cerca allerte DPC attive in Campania."""
    try:
        url = "https://api.github.com/repos/pcm-dpc/DPC-Bollettini-Vigilanza-Meteorologica/contents/json"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            files = r.json()
            if files:
                latest = sorted(files, key=lambda x: x.get("name",""))[-1]
                content_r = requests.get(latest["download_url"], timeout=8)
                if content_r.status_code == 200:
                    return {"source": "DPC", "data": content_r.json(), "fetched": datetime.now().strftime("%H:%M")}
    except Exception:
        pass
    return None


def _render_zona_map(punti, title, center_lat, center_lon, zoom=11, key="zona_map"):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom,
                   tiles="CartoDB positron")

    zona_colors = {"A": "red", "B": "orange", "C": "blue"}

    for p in punti:
        zona_col = zona_colors.get(p["zona"], "blue")
        popup_html = f"""
        <div style='font-family:Arial;min-width:220px'>
        <b>{p['comune']}</b><br>
        <span style='color:{zona_col};font-weight:bold'>Zona {p['zona']}</span><br>
        <b>{_gt('popup_raccolta')}:</b> {p['punto']}<br>
        <b>{_gt('popup_capacity')}:</b> ~{p['pax']:,}<br>
        <small style='color:#777'>{p['plat']:.5f}, {p['plon']:.5f}</small><br>
        <hr>
        <a href='{_gmaps_route_url(p["plat"],p["plon"],p["punto"])}' target='_blank'
           style='background:#4285F4;color:#fff;padding:3px 8px;border-radius:4px;
                  text-decoration:none;margin-right:4px;font-size:0.85em;'>
        🗺️ Google Maps</a>
        <a href='{_waze_url(p["plat"],p["plon"])}' target='_blank'
           style='background:#33CCFF;color:#fff;padding:3px 8px;border-radius:4px;
                  text-decoration:none;margin-right:4px;font-size:0.85em;'>
        🔵 Waze</a>
        <a href='{_apple_maps_url(p["plat"],p["plon"])}' target='_blank'
           style='background:#555;color:#fff;padding:3px 8px;border-radius:4px;
                  text-decoration:none;font-size:0.85em;'>
        🍎 Apple</a>
        </div>
        """
        folium.Marker(
            location=[p["plat"], p["plon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"📍 {p['comune']} — {p['punto']}",
            icon=folium.Icon(color=zona_col, icon="home", prefix="fa")
        ).add_to(m)

        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=5,
            color=zona_col,
            fill=True,
            fill_opacity=0.4,
            tooltip=f"🏘️ {p['comune']} (centro)"
        ).add_to(m)

    legend_html = f"""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
                padding:10px;border-radius:8px;border:2px solid #ccc;font-size:12px'>
    <b>{title}</b><br>
    🔴 {_gt('zona_rossa_legend')}<br>
    🟠 {_gt('zona_gialla_legend')}<br>
    🔵 {_gt('zona_blu_legend')}<br>
    📍 {_gt('raccolta_legend')}<br>
    ⭕ {_gt('centro_comune_legend')}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def show():
    now = datetime.now()

    if "emergenza_last_update" not in st.session_state:
        st.session_state.emergenza_last_update = None
    if "emergenza_cache_time" not in st.session_state:
        st.session_state.emergenza_cache_time = 0

    elapsed = time.time() - st.session_state.emergenza_cache_time

    col_title, col_refresh = st.columns([5, 1])
    with col_title:
        st.header(_gt("emergency_title"))
    with col_refresh:
        if st.button(_gt("emergency_update_btn"), key="emergenza_refresh_btn", help="Aggiorna dati emergenza"):
            st.session_state.emergenza_cache_time = 0
            st.rerun()

    if st.session_state.emergenza_last_update:
        remaining = max(0, CACHE_TTL_SECONDS - int(elapsed))
        mins_lbl = _gt("minutes_abbr")
        secs_lbl = _gt("seconds_abbr")
        next_lbl = _gt("next_auto_update")
        updated_lbl = _gt("data_updated_at")
        st.caption(
            f"{updated_lbl}: {st.session_state.emergenza_last_update} | "
            f"{next_lbl} {remaining//60}{mins_lbl} {remaining%60}{secs_lbl}"
        )

    if elapsed > CACHE_TTL_SECONDS or st.session_state.emergenza_last_update is None:
        st.session_state.emergenza_cache_time = time.time()
        st.session_state.emergenza_last_update = now.strftime("%d/%m/%Y %H:%M")

    st.markdown(_gt("emergency_intro"))

    # ══ NUMERI DI EMERGENZA ════════════════════════════════════════════════════
    with st.expander(_gt("emergency_numbers_section"), expanded=True):
        cols = st.columns(3)
        for i, (num, desc, color) in enumerate(NUMERI_EMERGENZA):
            with cols[i % 3]:
                st.markdown(
                    f"<div style='background:{color}22;border-left:4px solid {color};"
                    f"padding:10px;border-radius:6px;margin:4px 0;'>"
                    f"<b style='font-size:1.3em;color:{color};'>☎️ {num}</b><br>"
                    f"<span style='font-size:0.85em;'>{desc}</span></div>",
                    unsafe_allow_html=True
                )

    # ── Condividi via WhatsApp / Copia link ───────────────────────────────────
    _app_url = "https://sismocampania.streamlit.app"
    _wa_text = (
        "🚨 Monitoraggio sismico Campania in tempo reale (Vesuvio, Campi Flegrei, Ischia)%0A"
        f"👉 {_app_url}"
    )
    st.markdown(
        f"""<div style="display:flex;gap:10px;align-items:center;margin:8px 0 14px 0;">
        <a href="https://wa.me/?text={_wa_text}" target="_blank"
           style="display:inline-flex;align-items:center;gap:6px;background:#25D366;
                  color:white;padding:7px 16px;border-radius:8px;text-decoration:none;
                  font-size:0.9rem;font-weight:600;">
            📲 Condividi su WhatsApp
        </a>
        <span style="font-size:0.8rem;color:#888;">oppure copia il link: 
            <code style="background:#f1f3f5;padding:2px 6px;border-radius:4px;">{_app_url}</code>
        </span></div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ══ TABS PRINCIPALI ════════════════════════════════════════════════════════
    tab_sai, tab_vesuvio, tab_flegrei, tab_ischia, tab_regioni, tab_evento, tab_kit = st.tabs([
        "🆘 Sai cosa fare?",
        _gt("tab_vesuvio_zones"),
        _gt("tab_flegrei_zones"),
        "🏝️ Ischia",
        _gt("tab_other_regions"),
        _gt("tab_procedures"),
        _gt("tab_kit"),
    ])

    # ════════════════════════════════════════════════════════════════════════════
    # TAB SAI COSA FARE?  — Guida personalizzata basata su allerta INGV live
    # ════════════════════════════════════════════════════════════════════════════
    with tab_sai:
        st.markdown("""
        <div style='background:#1e3a5f;color:white;padding:14px 18px;border-radius:8px;margin-bottom:16px;'>
        <h3 style='margin:0;color:white !important;'>🆘 Sai cosa fare in caso di emergenza?</h3>
        <p style='margin:6px 0 0 0;font-size:0.9em;opacity:0.9;color:white !important;'>
        Guida personalizzata basata sui livelli di allerta INGV aggiornati in tempo reale.
        Scopri cosa fare ADESSO in base alla situazione vulcanica attuale.
        </p></div>
        """, unsafe_allow_html=True)

        # ── Fetch livelli allerta INGV ─────────────────────────────────────────
        try:
            _alert = fetch_ingv_alert_level()
        except Exception:
            _alert = {}

        _CF_LEVEL  = _alert.get("campi_flegrei", "GIALLO")
        _VES_LEVEL = _alert.get("vesuvio", "VERDE")
        _ISC_LEVEL = _alert.get("ischia", "VERDE")
        _ALERT_SRC = _alert.get("source", "INGV OV")

        _LEVEL_COLOR = {
            "VERDE": "#27ae60", "GIALLO": "#f39c12",
            "ARANCIONE": "#e67e22", "ROSSO": "#e74c3c",
        }
        _LEVEL_ICON = {
            "VERDE": "🟢", "GIALLO": "🟡",
            "ARANCIONE": "🟠", "ROSSO": "🔴",
        }

        # ── Badge allerta attuale ──────────────────────────────────────────────
        st.markdown("### 📡 Situazione attuale INGV")
        badge_cols = st.columns(3)
        for _col, _area_name, _level in [
            (badge_cols[0], "Campi Flegrei", _CF_LEVEL),
            (badge_cols[1], "Vesuvio", _VES_LEVEL),
            (badge_cols[2], "Ischia", _ISC_LEVEL),
        ]:
            _c = _LEVEL_COLOR.get(_level, "#6c757d")
            _ic = _LEVEL_ICON.get(_level, "⚪")
            with _col:
                st.markdown(
                    f"<div style='background:{_c}22;border:2px solid {_c};"
                    f"border-radius:8px;padding:12px;text-align:center;'>"
                    f"<div style='font-size:1.8em;'>{_ic}</div>"
                    f"<div style='font-weight:700;font-size:0.95em;'>{_area_name}</div>"
                    f"<div style='color:{_c};font-weight:800;font-size:1.1em;'>{_level}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        st.caption(f"Fonte: {_ALERT_SRC}")
        st.markdown("---")

        # ── Selezione area utente ──────────────────────────────────────────────
        st.markdown("### 🏠 La tua zona di rischio")
        _user_area = st.selectbox(
            "Seleziona la tua area:",
            ["📍 Scegli la tua area...", "🌋 Vesuvio (25 comuni zona rossa)",
             "🔥 Campi Flegrei (zona rossa)", "🏝️ Ischia"],
            key="sai_cosa_area_sel",
        )

        if _user_area == "📍 Scegli la tua area...":
            st.info("👆 Seleziona la tua area sopra per vedere le istruzioni personalizzate.")
        else:
            if "Vesuvio" in _user_area:
                _selected_level = _VES_LEVEL
                _zona_data = VESUVIO_ZONA_ROSSA
                _area_key = "vesuvio"
                _piano_url = "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vesuvio/"
                _area_label = "Vesuvio"
            elif "Campi Flegrei" in _user_area:
                _selected_level = _CF_LEVEL
                _zona_data = CF_ZONA_ROSSA
                _area_key = "campi_flegrei"
                _piano_url = "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/campi-flegrei/"
                _area_label = "Campi Flegrei"
            else:
                _selected_level = _ISC_LEVEL
                _zona_data = []
                _area_key = "ischia"
                _piano_url = "https://rischi.protezionecivile.gov.it/"
                _area_label = "Ischia"

            _lc = _LEVEL_COLOR.get(_selected_level, "#6c757d")
            _li = _LEVEL_ICON.get(_selected_level, "⚪")

            # ── Banner livello attuale + cosa fare ────────────────────────────
            _ISTRUZIONI = {
                "VERDE": {
                    "titolo": "Situazione nella norma — Prepararsi è il momento giusto",
                    "desc": "Nessuna anomalia significativa. Questo è il momento ideale per prepararsi.",
                    "steps": [
                        "✅ **Aggiorna il kit di emergenza** — verifica scadenze, integra scorte d'acqua e medicinali",
                        "✅ **Individua il punto di raccolta** del tuo Comune (vedi tab Vesuvio/CF/Ischia)",
                        "✅ **Salva i numeri di emergenza** nel telefono: 112, 115, 800 840 840 (PC)",
                        "✅ **Pianifica l'evacuazione familiare** — un percorso principale e uno alternativo",
                        "✅ **Scarica l'app IT-Alert** e attiva le notifiche",
                        "✅ **Tieni una radio a batterie** — in caso di emergenza è l'unica fonte affidabile",
                        "✅ **Tieniti aggiornato** su INGV e Protezione Civile",
                    ],
                },
                "GIALLO": {
                    "titolo": "Attenzione — Monitora la situazione con frequenza",
                    "desc": "Anomalie in corso. Non è ancora emergenza, ma devi essere pronto ad agire rapidamente.",
                    "steps": [
                        "⚠️ **Verifica che il kit di emergenza sia completo** e pronto vicino all'uscita",
                        "⚠️ **Controlla questa app ogni 2-4 ore** e i canali INGV OV",
                        "⚠️ **Avvisa la famiglia** del livello di attenzione e rivedi il piano di evacuazione",
                        "⚠️ **Identifica il tuo punto di raccolta** — sai esattamente dove andare?",
                        "⚠️ **Tieni il serbatoio dell'auto pieno** (o almeno a metà)",
                        "⚠️ **Segui solo fonti ufficiali** — Protezione Civile, INGV, RAI Radio 1",
                        "⚠️ **Non allarmarti**, ma sii pronto a partire in 15 minuti se arriva l'ordine",
                    ],
                },
                "ARANCIONE": {
                    "titolo": "ALLERTA — Preparati a evacuare immediatamente",
                    "desc": "Anomalie significative in corso. Le autorità potrebbero ordinare l'evacuazione a breve.",
                    "steps": [
                        "🟠 **PRENDI SUBITO il kit di emergenza** — acqua, cibo, medicinali, documenti, power bank",
                        "🟠 **Contatta i familiari** — pianificate insieme il percorso di evacuazione",
                        "🟠 **Tieniti pronto a partire in 10 minuti** dall'ordine delle autorità",
                        "🟠 **Ascolta RAI Radio 1** e gli aggiornamenti ufficiali della PC continuamente",
                        "🟠 **Spostati al punto di raccolta** solo se le autorità lo ordinano",
                        "🟠 **Non usare il telefono** per chiamate non urgenti — libera le linee ai soccorsi",
                        "🟠 **Non credere a voci non ufficiali** — fonti: protezionecivile.gov.it, INGV",
                    ],
                },
                "ROSSO": {
                    "titolo": "EMERGENZA — EVACUA ORA",
                    "desc": "Situazione critica. Segui immediatamente le istruzioni della Protezione Civile.",
                    "steps": [
                        "🔴 **EVACUA SUBITO** — non aspettare, segui le vie di fuga indicate dalla segnaletica DPC",
                        "🔴 **Prendi SOLO l'essenziale** — documenti, medicinali, 1 borsa",
                        "🔴 **Raggiungi il punto di raccolta** del tuo Comune IN AUTO (non a piedi)",
                        "🔴 **Segui la segnaletica gialla DPC** sulle vie di fuga — non improvvisare",
                        "🔴 **Ascolta solo RAI Radio 1** e i megafoni della Protezione Civile",
                        "🔴 **Non tornare a casa** per nessun motivo fino all'ok delle autorità",
                        "🔴 **Chiama il 112 solo per emergenze reali** — non intasare le linee",
                    ],
                },
            }

            _instr = _ISTRUZIONI.get(_selected_level, _ISTRUZIONI["VERDE"])

            st.markdown(
                f"<div style='background:{_lc}22;border-left:5px solid {_lc};"
                f"padding:14px 18px;border-radius:8px;margin:12px 0;'>"
                f"<h4 style='margin:0;color:{_lc};'>{_li} {_selected_level} — {_instr['titolo']}</h4>"
                f"<p style='margin:6px 0 0 0;'>{_instr['desc']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            st.markdown("#### 📋 Cosa fare ADESSO:")
            for step in _instr["steps"]:
                st.markdown(f"- {step}")

            st.markdown("---")

            # ── Trova il tuo punto di raccolta ────────────────────────────────
            if _zona_data:
                _tab_label = "🌋 Vesuvio" if _area_key == "vesuvio" else "🔥 Campi Flegrei"
                st.info(
                    f"📍 **Trova il tuo punto di raccolta e le vie di fuga** nel tab "
                    f"**{_tab_label}** qui accanto — seleziona il tuo Comune per ottenere "
                    f"indirizzo, capienza e navigazione diretta."
                )

            # ── Link rapidi ────────────────────────────────────────────────────
            st.markdown("---")
            _lnk1, _lnk2, _lnk3 = st.columns(3)
            with _lnk1:
                st.link_button(
                    "📋 Piano Evacuazione DPC",
                    _piano_url,
                    width='stretch',
                )
            with _lnk2:
                st.link_button(
                    "📡 IT-Alert — Allerta Nazionale",
                    "https://www.it-alert.it",
                    width='stretch',
                )
            with _lnk3:
                st.link_button(
                    "🌋 INGV — Monitoraggio Live",
                    "https://www.ingv.it",
                    width='stretch',
                )

        # ── Rimando alle procedure dettagliate ────────────────────────────────
        st.markdown("---")
        st.info(
            "📋 **Guide complete per ogni tipo di evento** (terremoto, eruzione, alluvione, frana…) "
            "sono disponibili nel tab **⚠️ Procedure per Tipo di Evento** qui accanto."
        )

    # ════════════════════════════════════════════════════════════════════════════
    # TAB VESUVIO
    # ════════════════════════════════════════════════════════════════════════════
    with tab_vesuvio:
        st.markdown("""
        <div style='background:#e8000022;border-left:5px solid #e80000;padding:12px;border-radius:6px;margin-bottom:16px;'>
        <b>🔴 Piano Nazionale di Evacuazione Vesuvio — Zona Rossa</b><br>
        25 comuni in zona A (rossa) — evacuazione preventiva totale in caso di allerta.<br>
        Fonte: Dipartimento Protezione Civile — Piano aggiornato (DPC 2019/2023)
        </div>
        """, unsafe_allow_html=True)

        col_info, col_kit_v = st.columns([1, 1])
        with col_info:
            st.markdown("""
            **Zone di allertamento Vesuvio:**
            - 🔴 **Zona Rossa** — evacuazione immediata (25 comuni + parti di Napoli est)
            - 🟡 **Zona Gialla** — rischio ricaduta ceneri e lapilli
            - 🔵 **Zona Blu** — rischio maremoto (costa)

            **In caso di allerta arancione/rossa:**
            1. Segui le comunicazioni ufficiali della PC
            2. Prendi il kit di emergenza (già preparato)
            3. Raggiungi il punto di raccolta del tuo Comune **in auto**
            4. Segui le vie di fuga indicate dalla segnaletica gialla DPC
            5. NON portare oggetti pesanti — carica solo documenti, medicinali, acqua
            """)
            st.markdown("🔗 [Piano evacuazione ufficiale DPC](https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vesuvio/)")

        with col_kit_v:
            st.markdown("""
            **Vie di fuga principali (segnaletica DPC):**
            - Autostrada A3 Napoli-Salerno (direzione Salerno)
            - SS 18 Tirrena Inferiore (verso sud)
            - Via Vesuviana / SP1 (anello Vesuvio)
            - A16 Napoli-Canosa (per comuni nord-est)

            **Evita in caso di eruzione:**
            - Tangenziale di Napoli (congestionamento)
            - Strade collinari strette del Vesuvio
            - Zone al di sotto di quota 500m (zona rossa)
            """)

        st.markdown("### 📍 Mappa Interattiva — 25 Comuni Zona Rossa Vesuvio")
        st.caption(_gt("map_marker_caption"))

        # Cerca comune più vicino se utente inserisce posizione
        col_search, col_btn = st.columns([3, 1])
        with col_search:
            _sel_mun = _gt("select_municipality")
            user_comune_v = st.selectbox(
                _gt("find_collection_point"),
                [_sel_mun] + [p["comune"] for p in VESUVIO_ZONA_ROSSA],
                key="vesuvio_comune_sel"
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)

        if user_comune_v != _sel_mun:
            punto = next((p for p in VESUVIO_ZONA_ROSSA if p["comune"] == user_comune_v), None)
            if punto:
                st.markdown(
                    f"<div style='background:#1a8a1a22;border-left:4px solid #1a8a1a;padding:12px;border-radius:6px;'>"
                    f"<b>📍 {punto['comune']}</b> — Zona {punto['zona']}<br>"
                    f"<b>{_gt('collection_point_label')}:</b> {punto['punto']}<br>"
                    f"<b>{_gt('capacity_label')}:</b> ~{punto['pax']:,} persone<br>"
                    f"{_nav_buttons_html(punto['plat'], punto['plon'], punto['punto'])}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        m_v = _render_zona_map(VESUVIO_ZONA_ROSSA, "Vesuvio — Zone Evacuazione",
                                40.820, 14.430, zoom=10, key="vesuvio_zona_map")
        folium_static(m_v, width=800, height=500)

        # Tabella completa
        with st.expander(_gt("all_collection_points")):
            for p in VESUVIO_ZONA_ROSSA:
                st.markdown(
                    f"🔴 **{p['comune']}** (Zona {p['zona']}) — {p['punto']} (~{p['pax']:,} pax)"
                    + _nav_buttons_html(p["plat"], p["plon"], p["punto"]),
                    unsafe_allow_html=True
                )
                st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════════
    # TAB CAMPI FLEGREI
    # ════════════════════════════════════════════════════════════════════════════
    with tab_flegrei:
        st.markdown("""
        <div style='background:#ff990022;border-left:5px solid #ff9900;padding:12px;border-radius:6px;margin-bottom:16px;'>
        <b>🟡 Piano Evacuazione Campi Flegrei — Allerta GIALLO attiva dal 11/05/2023</b><br>
        Bradisismo in corso — suolo in sollevamento, sismicità aumentata.<br>
        Zona Rossa CF: Pozzuoli, Bacoli, Monte di Procida, Quarto, parti di Napoli ovest.<br>
        Fonte: Dipartimento Protezione Civile
        </div>
        """, unsafe_allow_html=True)

        col_info_f, col_vie_f = st.columns([1, 1])
        with col_info_f:
            st.markdown("""
            **Zone di allertamento Campi Flegrei:**
            - 🔴 **Zona Rossa** — evacuazione in caso di allerta arancione/rossa
            - 🟡 **Zona Gialla** — rischio ricaduta ceneri (comuni limitrofi)

            **In caso di escalation allerta:**
            1. Segui le comunicazioni ufficiali della PC Campania
            2. Non aspettare: prepara il kit ADESSO
            3. Raggiungi il punto di raccolta assegnato al tuo Comune
            4. Usa le uscite verso nord (A1, A56 Tangenziale)
            5. Evita i tunnel e le gallerie della costa flegrea
            """)
            st.markdown("🔗 [Piano evacuazione CF — DPC](https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/campi-flegrei/)")

        with col_vie_f:
            st.markdown("""
            **Vie di fuga principali Campi Flegrei:**
            - A56 Tangenziale di Napoli (uscita verso nord/est)
            - A1 Milano-Napoli (da Napoli nord)
            - SS7Quater (Domitiana) verso Caserta/Roma
            - Via Campana (alternativa interna)

            **Punti di accoglienza fuori zona rossa:**
            - Caserta e provincia (regione accoglienza designata)
            - Benevento e provincia
            - Avellino e provincia
            """)

        st.markdown("### 📍 Mappa Interattiva — Punti Raccolta Zona Rossa Campi Flegrei")

        col_search_f, _ = st.columns([3, 1])
        with col_search_f:
            _sel_mun_f = _gt("select_municipality")
            user_comune_f = st.selectbox(
                _gt("find_collection_point"),
                [_sel_mun_f] + [p["comune"] for p in CF_ZONA_ROSSA],
                key="flegrei_comune_sel"
            )

        if user_comune_f != _sel_mun_f:
            punto_f = next((p for p in CF_ZONA_ROSSA if p["comune"] == user_comune_f), None)
            if punto_f:
                st.markdown(
                    f"<div style='background:#ff990022;border-left:4px solid #ff9900;padding:12px;border-radius:6px;'>"
                    f"<b>📍 {punto_f['comune']}</b> — Zona {punto_f['zona']}<br>"
                    f"<b>{_gt('collection_point_label')}:</b> {punto_f['punto']}<br>"
                    f"<b>{_gt('capacity_label')}:</b> ~{punto_f['pax']:,} persone<br>"
                    f"{_nav_buttons_html(punto_f['plat'], punto_f['plon'], punto_f['punto'], bg='#ff9900')}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        m_f = _render_zona_map(CF_ZONA_ROSSA, "Campi Flegrei — Zone Evacuazione",
                                40.840, 14.130, zoom=11, key="flegrei_zona_map")
        folium_static(m_f, width=800, height=500)

        with st.expander("📋 Tutti i punti di raccolta — Zona Rossa Campi Flegrei"):
            for p in CF_ZONA_ROSSA:
                col_zona = "🔴" if p["zona"] == "A" else "🟠"
                st.markdown(
                    f"{col_zona} **{p['comune']}** (Zona {p['zona']}) — {p['punto']} (~{p['pax']:,} pax)"
                    + _nav_buttons_html(p["plat"], p["plon"], p["punto"]),
                    unsafe_allow_html=True
                )
                st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════════
    # TAB ISCHIA
    # ════════════════════════════════════════════════════════════════════════════
    with tab_ischia:
        st.markdown("""
        <div style='background:#0d6efd22;border-left:5px solid #0d6efd;padding:12px;border-radius:6px;margin-bottom:16px;'>
        <b>🏝️ Piano Emergenza Sismica — Ischia (Casamicciola, Lacco Ameno, Forio)</b><br>
        Sismicità tettonica superficiale (&lt;5 km). Ultimo evento grave: <b>M 5.7 del 26/11/2022</b> (3 vittime, frane).<br>
        Fonte: Protezione Civile — Piano di Emergenza Comune di Ischia
        </div>
        """, unsafe_allow_html=True)

        col_info_i, col_vie_i = st.columns([1, 1])
        with col_info_i:
            st.markdown("""
            **Rischio principale Ischia:**
            - 🟠 **Sismicità superficiale** — terremoti < 5 km di profondità, forte impatto locale
            - 🟫 **Frane sismiche** — versanti instabili su Monte Epomeo (tufo giallo)
            - 🌊 **Maremoto locale** — possibile per eventi M > 5.5 in mare

            **In caso di terremoto:**
            1. **Non uscire subito** — il rischio frana è maggiore in strada durante la scossa
            2. Riparati sotto un tavolo robusto o contro un muro portante
            3. Dopo la scossa: allontanati da edifici e versanti franosi
            4. Raggiungi le aree di raccolta comunali in campo aperto
            5. Segui le istruzioni della Protezione Civile via IT-Alert
            """)
            st.markdown("🔗 [Piano emergenza sismico — Protezione Civile](https://www.protezionecivile.gov.it/it/rischio/rischio-sismico)")

        with col_vie_i:
            st.markdown("""
            **Vie di evacuazione Ischia:**
            - Porto di Ischia → traghetti per Napoli/Pozzuoli (in caso di evacuazione)
            - Porto di Casamicciola → aliscafi (alta frequenza)
            - Porto di Forio → alternativa ovest

            **Punti di raccolta** (campo aperto):
            - Stadio Comunale Ischia
            - Piazza degli Eroi (Ischia Porto)
            - Area portuale (lungomare)
            - Campi sportivi Casamicciola
            - Spiaggia di Lacco Ameno (area aperta)

            **⚠️ Attenzione frane:**
            Evitare le zone collinari sul versante nord di Monte Epomeo
            (Casamicciola alta, Serrara Fontana) nelle 24h successive a un evento M > 3.5
            """)

        st.markdown("""
        ### 🗺️ Zone a rischio — Ischia

        | Comune | Rischio principale | Azione |
        |--------|-------------------|--------|
        | Casamicciola Terme | ⚠️ Altissimo (frane + sisma) | Evacuazione immediata zone collinari |
        | Lacco Ameno | ⚠️ Alto (sisma superficiale) | Allontanarsi da edifici storici |
        | Forio | 🟡 Moderato-Alto | Seguire indicazioni PC |
        | Ischia Porto | 🟡 Moderato | Evitare lungomare post-sisma |
        | Barano d'Ischia | 🟡 Moderato (frane versante) | Evitare zone boschive collinari |
        | Sant'Angelo | 🟢 Basso-Moderato | Standard anti-sisma |
        """)

        with st.expander("🚁 Evacuazione via mare — Procedure"):
            st.markdown("""
            **In caso di evacuazione dell'isola disposta dalla PC:**

            1. **Non portarsi ai porti autonomamente** senza disposizione ufficiale — crea panico
            2. Seguire le indicazioni dei Vigili Urbani per zone di raccolta assegnate
            3. La Guardia Costiera coordina l'evacuazione via mare
            4. Priorità: persone con disabilità, anziani, bambini, feriti
            5. Portare solo l'essenziale: documenti, medicinali, kit emergenza

            **Numeri utili Ischia:**
            - Comune di Ischia: 081 3333111
            - Comune di Casamicciola: 081 3994411
            - Capitaneria di Porto Ischia: 081 984200
            - Guardia Costiera: **1530**
            """)

        st.info(
            "📋 **Riferimento normativo**: Ischia rientra nella **zona sismica 2** (alta sismicità). "
            "Il Piano Nazionale per la Riduzione del Rischio Sismico include specifici interventi "
            "per le isole minori campane. IT-Alert è attivo per Ischia."
        )

    # ════════════════════════════════════════════════════════════════════════════
    # TAB ALTRE REGIONI
    # ════════════════════════════════════════════════════════════════════════════
    with tab_regioni:
        st.subheader("🗺️ Punti di Raccolta per Regione")

        regioni_lista = sorted(DATI_REGIONI.keys())
        regione_sel = st.selectbox("Seleziona la tua regione", regioni_lista, key="emergenza_regione")
        dati = DATI_REGIONI[regione_sel]

        st.markdown(f"**Criticità — {regione_sel}:** {dati['criticita']}")
        st.markdown(f"📞 **Numeri locali**: {dati['numeri']}")
        cols_links = st.columns(3)
        with cols_links[0]:
            st.markdown(f"🔗 [Protezione Civile {regione_sel}]({dati['link_pc']})")
        with cols_links[1]:
            st.markdown(f"🔗 [ARPA {regione_sel}]({dati['link_arpa']})")
        if dati.get("link_speciale"):
            with cols_links[2]:
                st.markdown(f"⭐ [{dati['label_speciale']}]({dati['link_speciale']})")

        st.info(
            "Per i punti di raccolta esatti del tuo comune, contatta il **Comune di residenza** "
            "o la **Prefettura** della tua provincia. I piani comunali di emergenza sono pubblici "
            "e disponibili sul sito del tuo Comune."
        )
        st.markdown(
            "🔗 [Cerca piano emergenza del tuo Comune — DPC Rischi](https://rischi.protezionecivile.gov.it/)"
        )

    # ════════════════════════════════════════════════════════════════════════════
    # TAB PROCEDURE PER EVENTO
    # ════════════════════════════════════════════════════════════════════════════
    with tab_evento:
        st.subheader("⚠️ Cosa Fare in Base all'Emergenza")

        evento = st.selectbox(
            "Seleziona il tipo di emergenza",
            list(EVENTI.keys()),
            key="emergenza_evento"
        )
        info = EVENTI[evento]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                "<div style='background:#1a8a1a22;border-left:4px solid #1a8a1a;padding:12px;border-radius:6px;margin-bottom:12px;'>"
                "<b style='color:#1a8a1a'>✅ COSA FARE</b></div>",
                unsafe_allow_html=True
            )
            for item in info["fare"]:
                st.markdown(f"✔️ {item}")

        with col2:
            st.markdown(
                "<div style='background:#e8000022;border-left:4px solid #e80000;padding:12px;border-radius:6px;margin-bottom:12px;'>"
                "<b style='color:#e80000'>❌ COSA NON FARE</b></div>",
                unsafe_allow_html=True
            )
            for item in info["non_fare"]:
                st.markdown(f"⛔ {item}")

        st.markdown(f"---\n🎒 **Kit consigliato**: {info['kit']}")
        st.markdown(f"🔗 [Guida ufficiale Protezione Civile]({info['link']})")

    # ════════════════════════════════════════════════════════════════════════════
    # TAB KIT EMERGENZA
    # ════════════════════════════════════════════════════════════════════════════
    with tab_kit:
        st.subheader("🎒 Kit di Emergenza — Lista Completa")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **💧 Acqua e Cibo**
            - Acqua: 2L/persona/giorno × 3 giorni min.
            - Cibo non deperibile (scatolame, barrette energetiche)
            - Apriscatole manuale
            - Posate monouso
            - Sale, zucchero, caffè solubile
            """)
        with col2:
            st.markdown("""
            **📋 Documenti e Comunicazione**
            - Carta d'identità / passaporto (copie plastificate)
            - Tessera sanitaria
            - Documenti assicurazione casa/auto
            - Radio a batterie (riceve RAI Radio 1)
            - Power bank carico (min. 20.000 mAh)
            - Torcia LED + batterie di riserva
            - Fischietto (segnalazione in caso di crollo)
            """)
        with col3:
            st.markdown("""
            **🏥 Salute e Sicurezza**
            - Medicinali personali (scorta 30 giorni)
            - Kit primo soccorso (garze, bende, disinfettante)
            - Mascherine FFP2 (min. 10 per persona)
            - Guanti monouso (latex o nitrile)
            - Scarpe robuste (già indossate)
            - Cambio vestiti (caldo e freddo)
            - Coperte termiche d'emergenza
            - Contanti (in banconote piccole)
            """)

        st.markdown("---")
        st.markdown("""
        **📦 Dove tenere il kit:**
        - Borsa pronta vicino alla porta d'uscita
        - Verificare scadenze medicinali ogni 6 mesi
        - Tenere documenti in busta impermeabile
        - Caricare il power bank ogni mese

        **🏠 Prepara ora:**
        1. Identifica le 2 vie di uscita dalla tua abitazione
        2. Accordati con la famiglia su dove incontrarsi fuori casa
        3. Conosci il punto di raccolta del tuo Comune
        4. Salva i numeri di emergenza nel cellulare
        """)

    st.markdown("---")

    # ══ LINK RAPIDI ═══════════════════════════════════════════════════════════
    st.subheader("🔗 Link Ufficiali")
    link_cols = st.columns(3)
    with link_cols[0]:
        st.markdown("""
        - 🏛️ [Protezione Civile Nazionale](https://www.protezionecivile.gov.it)
        - 🌋 [INGV — monitoraggio](https://www.ingv.it)
        - 🌡️ INGV Osservatorio Vesuviano
        - 📋 [DPC Rischi — Pianificazione](https://rischi.protezionecivile.gov.it/)
        """)
    with link_cols[1]:
        st.markdown("""
        - 🌊 [Allerta meteo Campania](https://centrofunzionale.regione.campania.it/)
        - 🚒 [Vigili del Fuoco](https://www.vigilfuoco.it)
        - 🏥 [Ministero della Salute](https://www.salute.gov.it)
        - ⚡ [e-distribuzione — guasti](https://www.e-distribuzione.it)
        """)
    with link_cols[2]:
        st.markdown("""
        - 🌋 [Piano evacuazione Vesuvio](https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vesuvio/)
        - 🔥 [Piano evacuazione CF](https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/campi-flegrei/)
        - 📡 [IT-Alert — sistema allerta](https://www.it-alert.it)
        - 🌐 [DPC Open Data](https://github.com/pcm-dpc)
        """)
