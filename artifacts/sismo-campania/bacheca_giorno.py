"""
Bacheca del Giorno — Comunità SismoCampania
Auto-aggiornante ogni giorno alle mezzanotte.
  1. ✝️  Santo/a del giorno   — calendario liturgico italiano con note campane
  2. 🕰️  Oggi nella storia   — eventi sismici/vulcanici campani per questo giorno
  3. 🌋  Curiosità vulcanologica — generata dall'AI (o pool di fallback)
"""

from __future__ import annotations
import os
import hashlib
import streamlit as st
from datetime import date as _date, datetime as _dt

# ─────────────────────────────────────────────────────────────────────────────
# 1. SANTO/A DEL GIORNO
# ─────────────────────────────────────────────────────────────────────────────

_SANTI: dict[tuple[int, int], tuple[str, str | None]] = {
    # Gennaio
    (1,  1): ("Santa Maria Madre di Dio",        None),
    (1,  2): ("Santi Basilio e Gregorio",         None),
    (1,  3): ("Santissimo Nome di Gesù",          None),
    (1,  5): ("San Giovanni Nepomuceno",          None),
    (1,  6): ("Epifania del Signore",             "Festa nazionale"),
    (1,  7): ("San Raimondo de Peñafort",         None),
    (1, 10): ("San Gregorio di Nissa",            None),
    (1, 13): ("Sant'Ilario di Poitiers",          None),
    (1, 17): ("Sant'Antonio Abate",               "Patrono degli animali; benedizione degli animali in tutta Italia"),
    (1, 20): ("San Sebastiano",                   "Martire romano, patrono degli atleti"),
    (1, 21): ("Sant'Agnese",                      "Giovane martire romana"),
    (1, 24): ("San Francesco di Sales",           "Patrono dei giornalisti e scrittori"),
    (1, 25): ("Conversione di San Paolo",         "L'apostolo cambia vita sulla via di Damasco"),
    (1, 26): ("Santi Timoteo e Tito",             None),
    (1, 28): ("San Tommaso d'Aquino",             "Patrono degli studenti e dei teologi, nato a Roccasecca (FR)"),
    (1, 31): ("San Giovanni Bosco",               "Patrono dei giovani e degli insegnanti"),
    # Febbraio
    (2,  2): ("Presentazione del Signore",        "Candelora — la metà dell'inverno"),
    (2,  3): ("San Biagio",                       "Patrono dei malati di gola"),
    (2,  5): ("Sant'Agata",                       "Patrona di Catania — protegge l'Etna dal fuoco"),
    (2, 10): ("Sant'Scolastica",                  "Sorella gemella di San Benedetto"),
    (2, 11): ("Beata Vergine di Lourdes",         None),
    (2, 14): ("San Valentino di Terni",           "Patrono degli innamorati"),
    (2, 22): ("Cattedra di San Pietro",           None),
    # Marzo
    (3,  7): ("Sante Perpetua e Felicita",        None),
    (3,  8): ("San Giovanni di Dio",              "Patrono degli infermi e degli ospedali"),
    (3, 17): ("San Patrizio",                     "Patrono dell'Irlanda"),
    (3, 19): ("San Giuseppe",                     "Sposo di Maria, patrono dei padri e dei lavoratori — festa nazionale"),
    (3, 25): ("Annunciazione del Signore",        "L'Angelo annuncia a Maria la nascita di Gesù"),
    # Aprile
    (4,  4): ("Sant'Isidoro di Siviglia",         None),
    (4, 23): ("San Giorgio",                      "Martire, patrono dell'Inghilterra e del Libano"),
    (4, 25): ("San Marco Evangelista",            "Patrono di Venezia — festa nazionale"),
    (4, 28): ("San Luigi Maria Grignon",          None),
    # Maggio
    (5,  1): ("San Giuseppe Lavoratore",          "Festa dei Lavoratori — festa nazionale"),
    (5,  3): ("Santi Filippo e Giacomo",          None),
    (5,  4): ("Sant'Antonino di Sorrento",        "🌋 Patrono di Sorrento, ai piedi del Vesuvio"),
    (5, 12): ("Santi Nereo e Achilleo",           None),
    (5, 15): ("San Casimiro",                     None),
    (5, 26): ("San Filippo Neri",                 "Patrono di Roma, fondatore dell'Oratorio"),
    (5, 31): ("Visitazione della Vergine Maria",  None),
    # Giugno
    (6,  2): ("Santi Marcellino e Pietro",        None),
    (6, 13): ("Sant'Antonio di Padova",           "Uno dei santi più amati in Italia, patrono dei poveri e dei viaggiatori"),
    (6, 21): ("San Luigi Gonzaga",                "Patrono della gioventù"),
    (6, 24): ("Natività di San Giovanni Battista","Precursore di Cristo — antichissima festa solstiziale"),
    (6, 28): ("Sant'Ireneo di Lione",             None),
    (6, 29): ("Santi Pietro e Paolo",             "Patroni di Roma — festa nazionale"),
    # Luglio
    (7,  3): ("San Tommaso Apostolo",             "L'apostolo che dubitava"),
    (7, 11): ("San Benedetto da Norcia",          "Patrono d'Europa, padre del monachesimo occidentale"),
    (7, 16): ("Beata Vergine del Carmelo",        "Madonna del Carmelo, venerata in tutta Campania"),
    (7, 22): ("Santa Maria Maddalena",            "Prima testimone della Resurrezione"),
    (7, 25): ("San Giacomo Apostolo",             "Patrono della Spagna, meta del Cammino di Santiago"),
    (7, 26): ("Santi Anna e Gioacchino",          "Genitori della Madonna, nonni di Gesù"),
    (7, 29): ("Santa Marta",                      None),
    (7, 31): ("Sant'Ignazio di Loyola",           "Fondatore della Compagnia di Gesù"),
    # Agosto
    (8,  4): ("San Giovanni Maria Vianney",       "Curé d'Ars, patrono dei parroci"),
    (8,  6): ("Trasfigurazione del Signore",      None),
    (8, 10): ("San Lorenzo",                      "Diacono e martire, 'pioggia di stelle cadenti' di San Lorenzo"),
    (8, 11): ("Santa Chiara d'Assisi",            "Fondatrice delle Clarisse"),
    (8, 15): ("Assunzione di Maria",              "Ferragosto — festa nazionale"),
    (8, 20): ("San Bernardo di Chiaravalle",      None),
    (8, 22): ("Beata Vergine Maria Regina",       None),
    (8, 24): ("San Bartolomeo Apostolo",
              "🌋 In questo giorno del 79 d.C. il Vesuvio eruttò seppellendo Pompei ed Ercolano sotto cenere e lapilli"),
    (8, 27): ("Santa Monica",                     "Madre di Sant'Agostino"),
    (8, 28): ("Sant'Agostino di Ippona",          "Uno dei Padri della Chiesa, filosofo e teologo"),
    # Settembre
    (9,  3): ("San Gregorio Magno",               "Papa e Dottore della Chiesa"),
    (9,  8): ("Natività della Beata Vergine Maria",None),
    (9, 13): ("San Giovanni Crisostomo",          None),
    (9, 14): ("Esaltazione della Santa Croce",    None),
    (9, 19): ("San Gennaro",
              "🌋 Patrono di Napoli — protegge la città dal Vesuvio. Il prodigioso scioglimento del sangue si ripete "
              "tre volte l'anno. San Gennaro è morto martire nel 305 d.C."),
    (9, 21): ("San Matteo Evangelista",           "Patrono di Salerno, apostolo ed esattore delle tasse"),
    (9, 22): ("San Maurizio e compagni",          None),
    (9, 29): ("Santi Michele, Gabriele e Raffaele","I tre Arcangeli — San Michele è patrono delle Forze Armate"),
    (9, 30): ("San Girolamo",                     "Traduttore della Bibbia in latino (Vulgata)"),
    # Ottobre
    (10,  1): ("Santa Teresa di Gesù Bambino",   "La 'piccola via', patrona delle missioni"),
    (10,  4): ("San Francesco d'Assisi",          "Patrono d'Italia e degli animali — giornata di benedizione degli animali"),
    (10,  7): ("Beata Vergine del Rosario",       "Istituita dopo la vittoria di Lepanto del 1571"),
    (10, 15): ("Santa Teresa d'Avila",            "Mistica, Dottore della Chiesa"),
    (10, 18): ("San Luca Evangelista",            "Patrono dei medici e dei pittori"),
    (10, 22): ("San Giovanni Paolo II",           "Papa polacco, beatificato nel 2011"),
    (10, 28): ("Santi Simone e Giuda Taddeo",    None),
    # Novembre
    (11,  1): ("Tutti i Santi",                   "Ognissanti — festa nazionale"),
    (11,  2): ("Commemorazione dei Defunti",      "Giorno dei Morti — si visitano i cimiteri"),
    (11,  3): ("San Martino de Porres",           None),
    (11,  4): ("San Carlo Borromeo",              "Patrono dei catechisti — festa nazionale fino al 1977"),
    (11, 11): ("San Martino di Tours",            "Festa dell'autunno e del vino novello: 'A San Martino ogni mosto diventa vino'"),
    (11, 22): ("Santa Cecilia",                   "Patrona dei musicisti e della musica sacra"),
    (11, 23): ("San Clemente I",
               "⚠️ Il 23/11/1980 alle 19:34 il terremoto dell'Irpinia (M6.9) devastò la Campania: 2.914 vittime, "
               "280.000 sfollati — la catastrofe sismica più grave d'Italia del dopoguerra"),
    (11, 25): ("Santa Caterina d'Alessandria",    "Patrona dei filosofi e degli studenti"),
    (11, 30): ("Sant'Andrea Apostolo",            "Patrono della Scozia e della Russia"),
    # Dicembre
    (12,  3): ("San Francesco Saverio",           "Grande missionario gesuita in Asia"),
    (12,  6): ("San Nicola di Bari",              "Il vero Babbo Natale — patrono dei bambini, marinai e viaggiatori"),
    (12,  7): ("Sant'Ambrogio",                   "Patrono di Milano — festa molto sentita in Lombardia"),
    (12,  8): ("Immacolata Concezione",           "Festa nazionale — processioni in tutta Italia"),
    (12, 12): ("Beata Vergine di Guadalupe",      None),
    (12, 13): ("Santa Lucia",                     "'Santa Lucia, la notte più lunga che ci sia' — solstizio arcaico"),
    (12, 16): ("San Eusebio di Vercelli",
               "🌋 Il 16/12/1631 il Vesuvio eruttò in modo catastrofico: 4.000 vittime, colate laviche fino al mare"),
    (12, 25): ("Natale del Signore",              "Gesù nasce a Betlemme — festa nazionale"),
    (12, 26): ("Santo Stefano",                   "Primo martire cristiano — festa nazionale"),
    (12, 27): ("San Giovanni Apostolo",           "L'apostolo 'amato da Gesù', autore del Vangelo e dell'Apocalisse"),
    (12, 28): ("Santi Innocenti Martiri",         "I bambini uccisi da Erode"),
    (12, 31): ("San Silvestro I",                 "Papa dal 314 al 335 — veglia di Capodanno"),
}


def _get_santo(today: _date) -> tuple[str, str | None]:
    """Ritorna (nome_santo, nota) per la data indicata."""
    entry = _SANTI.get((today.month, today.day))
    if entry:
        return entry
    nomi_mese = [
        "Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
        "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre",
    ]
    return (f"Beati e Santi del {today.day} {nomi_mese[today.month - 1]}", None)


# ─────────────────────────────────────────────────────────────────────────────
# 2. OGGI NELLA STORIA — Campania sismica e vulcanica
# ─────────────────────────────────────────────────────────────────────────────

_STORIA: dict[tuple[int, int], list[dict]] = {
    (1, 5): [
        {"anno": 1973, "testo": "Intensa crisi bradisismica ai Campi Flegrei: iniziano le misure di "
                                 "sollevamento sistematico del suolo a Pozzuoli.", "icona": "🌋"},
    ],
    (2, 4): [
        {"anno": 1980, "testo": "Forti scosse precursori ai Campi Flegrei. L'unità di crisi dell'Osservatorio "
                                 "Vesuviano inizia il monitoraggio continuo 24h.", "icona": "🛰️"},
    ],
    (3, 17): [
        {"anno": 1944, "testo": "L'ultima eruzione del Vesuvio: le colate laviche raggiungono San Sebastiano "
                                 "al Vesuvio e Massa di Somma. Oltre 26 soldati alleati morti. "
                                 "Da allora il Vesuvio è quiescente.", "icona": "🌋"},
    ],
    (4,  4): [
        {"anno": 1906, "testo": "Inizia la grande eruzione del Vesuvio del 1906 (4-24 aprile): "
                                 "la più violenta del XX secolo. Il pennacchio raggiunge 13 km d'altezza, "
                                 "piogge di cenere fino alla Calabria. 218 vittime.", "icona": "🌋"},
    ],
    (4, 17): [
        {"anno": 1982, "testo": "Decreto governativo di sgombero parziale di Pozzuoli: circa 40.000 persone "
                                 "evacuate dalla zona rossa del bradisismo. Il suolo si era sollevato "
                                 "di oltre 1,5 metri dal 1970.", "icona": "⚠️"},
    ],
    (5, 16): [
        {"anno": 1984, "testo": "Terremoto M4.2 ai Campi Flegrei durante il picco della seconda crisi "
                                 "bradisismica. Il sollevamento totale supera i 3,4 metri. Pozzuoli è "
                                 "quasi completamente evacuata.", "icona": "🔴"},
    ],
    (6, 22): [
        {"anno": 1910, "testo": "Terremoto di Potenza M5.8, fortemente avvertito in Campania. "
                                 "Danni ai centri abitati della Basilicata meridionale.", "icona": "🔴"},
    ],
    (7, 26): [
        {"anno": 1805, "testo": "Terremoto del Molise M6.6 (26 luglio 1805): violentissimo sisma "
                                 "avvertito in tutta la Campania e in metà Italia meridionale. "
                                 "Oltre 5.000 vittime.", "icona": "🔴"},
    ],
    (8, 21): [
        {"anno": 2017, "testo": "Terremoto M4.0 a Casamicciola Terme, Ischia: 2 vittime, 39 feriti, "
                                 "circa 2.600 sfollati. Gravi danni al centro storico di Casamicciola. "
                                 "L'isola è su una struttura vulcanica attiva.", "icona": "🔴"},
    ],
    (8, 24): [
        {"anno": 79, "testo": "Il Vesuvio erutta alle ore 13:00 circa, seppellendo Pompei sotto 6 metri "
                               "di lapilli e cenere, ed Ercolano sotto una colata piroclastica. "
                               "Tra 2.000 e 16.000 vittime. L'eruzione dura 18 ore. "
                               "Plinio il Giovane la descrive in una lettera rimasta storica.", "icona": "🌋"},
    ],
    (9, 19): [
        {"anno": 305, "testo": "Martirio di San Gennaro, vescovo di Benevento, decapitato a Pozzuoli "
                                "(zona Campi Flegrei) per ordine di Diocleziano. Diventerà il patrono "
                                "di Napoli e protettore dal Vesuvio.", "icona": "✝️"},
        {"anno": 1980, "testo": "Sciame sismico precursore ai Campi Flegrei. I sismografi dell'INGV OV "
                                 "registrano una decina di eventi M>1 in area flegrea.", "icona": "🛰️"},
    ],
    (9, 29): [
        {"anno": 1538, "testo": "Inizia l'eruzione che forma Monte Nuovo nei Campi Flegrei: "
                                 "in soli 2 giorni nasce un cono vulcanico alto 133 metri. "
                                 "Preceduta da settimane di terremoti e sollevamento del suolo. "
                                 "Ultima eruzione in area flegrea.", "icona": "🌋"},
    ],
    (10,  1): [
        {"anno": 1983, "testo": "Terremoto M4.0 ai Campi Flegrei nel pieno della crisi bradisismica "
                                 "1982-84. Le scosse diventano sempre più frequenti: oltre 1.600 eventi "
                                 "registrati solo in ottobre.", "icona": "🔴"},
    ],
    (11, 23): [
        {"anno": 1980, "testo": "TERREMOTO DELL'IRPINIA: ore 19:34, magnitudo M6.9. Epicentro "
                                 "tra Sant'Angelo dei Lombardi e Lioni (AV). "
                                 "2.914 vittime, 8.848 feriti, 280.000 sfollati. "
                                 "Il soccorso arriva con grave ritardo. La catastrofe sismica più grave "
                                 "d'Italia nel dopoguerra. Il sisma fu avvertito fino a Roma e Bari.", "icona": "🔴"},
    ],
    (11, 26): [
        {"anno": 2022, "testo": "Terremoto M5.9 a Casamicciola Terme (Ischia) alle ore 05:07. "
                                 "12 vittime, interi quartieri sepolti da frane. "
                                 "Il sisma è il più forte registrato sull'isola dal 1883. "
                                 "Ischia è un'isola vulcanica con pericolosità sismica elevata.", "icona": "🔴"},
    ],
    (12, 16): [
        {"anno": 1631, "testo": "La grande eruzione del Vesuvio del 1631: la più letale dal 79 d.C. "
                                 "Le colate laviche raggiungono il mare in più punti. "
                                 "Circa 4.000 vittime tra flussi piroclastici e alluvioni. "
                                 "L'eruzione dura 6 giorni. Da questa data il Vesuvio ha eruttato "
                                 "continuamente fino al 1944.", "icona": "🌋"},
    ],
    (12, 19): [
        {"anno": 2023, "testo": "Terremoto M4.4 ai Campi Flegrei, il più forte dal 1984: ore 12:11. "
                                 "Avvertito in tutta l'area napoletana. Lievi danni a edifici storici "
                                 "nei Comuni della zona rossa. Accelerazione del bradisismo in corso.", "icona": "🔴"},
    ],
    (12, 28): [
        {"anno": 1908, "testo": "Terremoto di Messina M7.1: la più grave catastrofe naturale d'Italia. "
                                 "Oltre 80.000 vittime (stime fino a 200.000). "
                                 "Fortemente avvertito in tutta la Campania e il Sud Italia.", "icona": "🔴"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. CURIOSITÀ VULCANOLOGICA — pool di fallback + AI
# ─────────────────────────────────────────────────────────────────────────────

_CURIOSITA_POOL = [
    ("🌡️ Temperatura magma", "Il magma del Vesuvio può raggiungere i **1.200°C**. "
     "Per confronto, l'acciaio fonde a circa 1.370°C. La roccia basaltica del vulcano "
     "si solidifica a temperature intorno ai 700°C, formando la caratteristica lava nera."),
    ("⏱️ Velocità eruzioni", "Il Vesuvio è capace di emettere fino a **1,5 milioni di tonnellate** "
     "di materiale vulcanico al secondo nei picchi eruttivi. L'eruzione del 79 d.C. "
     "ha liberato energia pari a **100.000 bombe atomiche**."),
    ("📏 Bradisismo di Pozzuoli", "Dal 2005 ad oggi il suolo di Pozzuoli si è sollevato di oltre "
     "**160 cm** — a un ritmo che accelera ogni anno. In alcuni tratti del porto, "
     "i segni dell'innalzamento sono visibili sulle colonne del Serapeo romano, "
     "dove i molluschi marini hanno lasciato tracce fino a 7 metri d'altezza."),
    ("🕳️ Camera magmatica", "Sotto i Campi Flegrei si trovano **due serbatoi magmatici sovrapposti**: "
     "uno superficiale a circa 3 km di profondità (fonte dei terremoti del bradisismo) "
     "e uno più profondo tra 7 e 10 km. Il volume totale stimato è di alcune decine di km³."),
    ("🌊 Vesuvio e il mare", "Nel 79 d.C. la linea di costa era **circa 2 km più avanti** di oggi. "
     "Le colate piroclastiche dell'eruzione hanno aggiunto materiale al fondo del mare, "
     "spostando letteralmente la riva. Ercolano, oggi a 1,5 km dal mare, era un porto."),
    ("🔭 L'osservatorio più antico", "L'**Osservatorio Vesuviano** (1841) è il più antico osservatorio "
     "vulcanologico del mondo, fondato dal re Ferdinando II di Borbone. Originariamente "
     "ospitato su una struttura in muratura a 608 m di quota sul Vesuvio, oggi ha sede "
     "a Napoli ma gestisce oltre 250 stazioni di monitoraggio in Campania."),
    ("🏔️ Dimensioni Campi Flegrei", "Il supervulcano dei Campi Flegrei è una caldera di "
     "**12 km di diametro**, formata da due megaeruzioni: la Campanian Ignimbrite "
     "(39.000 anni fa, la più grande eruzione europea degli ultimi 200.000 anni) "
     "e l'Ignimbrite Neapolitana (15.000 anni fa). Il golfo di Pozzuoli è al centro della caldera."),
    ("💨 Gas e fumarole", "Ogni giorno la Solfatara emette circa **1.500 tonnellate** di CO₂ e "
     "centinaia di tonnellate di vapore acqueo e anidride solforosa. "
     "Le fumarole raggiungono i **160°C** al suolo. La quantità di gas è uno dei "
     "parametri monitorati dall'INGV per valutare lo stato del vulcano."),
    ("🌋 Ischia vulcanica", "Ischia è l'isola **più vulcanicamente attiva** dell'arco campano. "
     "Il Monte Epomeo (789 m) è un blocco di tufo sollevato dal bradisismo. "
     "L'ultima eruzione risale al **1302 d.C.**, ma l'attività idrotermale "
     "(acque termali calde) è continua e alimenta l'economia turistica dell'isola."),
    ("📡 Rete di monitoraggio", "L'INGV Osservatorio Vesuviano gestisce una rete di oltre "
     "**250 stazioni** in Campania: sismometri, GPS, clinometri, sensori gas, "
     "termocamere e webcam. I dati vengono trasmessi in tempo reale al Centro di "
     "Monitoraggio di Napoli, operativo **24 ore su 24, 365 giorni l'anno**."),
    ("🏛️ Pompei preservata", "Le vittime di Pompei non furono sepolte dalla lava, "
     "ma da una **pioggia di lapilli** alta 6 metri e poi da nubi ardenti piroclastiche. "
     "Il calore — oltre 300°C — uccise istantaneamente. La cenere ha conservato "
     "i corpi in modo così perfetto che possiamo vedere i volti delle vittime a distanza "
     "di quasi 2.000 anni."),
    ("🧪 Il 'sangue' di San Gennaro", "Il prodigio della liquefazione del sangue di San Gennaro "
     "è studiato dalla scienza dal 1902. Una teoria propone che si tratti di un "
     "**fluido tissotropico** — liquido a riposo, fluido sotto agitazione. "
     "I napoletani lo considerano un presagio: se il sangue non si scioglie, "
     "è segnale di disgrazie per la città."),
    ("🌍 Il rischio Vesuvio", "La Zona Rossa del Vesuvio comprende **18 comuni** e oltre "
     "**800.000 abitanti** — la più alta concentrazione di persone in area vulcanica "
     "ad alto rischio in Europa. Il piano di evacuazione prevede 72 ore per mettere "
     "in sicurezza tutta la popolazione."),
    ("⚡ Fulmini vulcanici", "Durante le grandi eruzioni vulcaniche si formano **fulmini vulcanici**: "
     "le particelle di cenere si caricano elettrostaticamente per attrito e generano "
     "scariche fino a 200.000 volt. Nell'eruzione del Calbuco (Cile, 2015) ne sono stati "
     "fotografati migliaia. Anche il Vesuvio ne genera durante le eruzioni esplosive."),
    ("🌊 Tsunami vulcanici", "Un'eruzione del Vesuvio potrebbe generare un **maremoto** nel "
     "Golfo di Napoli. L'eruzione del 79 d.C. ha prodotto onde anomale registrate fino "
     "alle coste africane. I vulcanologi monitorano anche il rischio tsunami per le "
     "isole di Ischia e Procida, esposte a scivolamenti sottomarini."),
]


@st.cache_data(ttl=86_400, show_spinner=False)
def _get_curiosita_ai(date_key: str) -> str | None:
    """
    Genera una curiosità vulcanologica via AI (Replit proxy).
    date_key = "YYYYMMDD" — usata come seed per la coerenza giornaliera.
    Ritorna il testo o None se l'AI non risponde.
    """
    argomenti = [
        "le eruzioni del Vesuvio nella storia",
        "il bradisismo dei Campi Flegrei",
        "i terremoti profondi e i terremoti vulcanici",
        "le fumarole e i gas vulcanici della Solfatara",
        "il monitoraggio sismico in tempo reale dell'INGV",
        "i piani di evacuazione per i vulcani campani",
        "la geologia dell'Isola d'Ischia",
        "le onde sismiche e come si propagano",
        "i super-vulcani e la caldera dei Campi Flegrei",
        "Plinio il Giovane e la descrizione dell'eruzione del 79 d.C.",
        "le rocce vulcaniche: tufo, basalto e pomice",
        "la scala Richter e la magnitudo momento",
        "i flussi piroclastici e la loro velocità",
        "la rete GPS per il monitoraggio della deformazione del suolo",
        "il rischio vulcanico in Italia rispetto al mondo",
    ]
    idx = int(hashlib.md5(date_key.encode()).hexdigest(), 16) % len(argomenti)
    argomento = argomenti[idx]

    try:
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        api_key  = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "replit-proxy")
        if not base_url:
            return None
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": (
                    "Sei un vulcanologo divulgativo italiano. Scrivi una curiosità affascinante "
                    "e accurata sul tema indicato, in massimo 4 frasi. Tono: scientifico ma "
                    "accessibile al grande pubblico. Concludi con un fatto sorprendente. "
                    "Rispondi SOLO con il testo della curiosità, senza titolo né formattazione."
                ),
            }, {
                "role": "user",
                "content": f"Scrivi una curiosità vulcanologica su: {argomento}",
            }],
            max_tokens=200,
            temperature=0.7,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text if len(text) > 30 else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# RENDER PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

def render_bacheca(today: _date | None = None) -> None:
    """
    Renderizza la Bacheca del Giorno — da chiamare dentro la sezione Comunità.
    Tre card: Santo, Storia, Curiosità AI.
    """
    if today is None:
        today = _date.today()

    mesi_it = [
        "gennaio","febbraio","marzo","aprile","maggio","giugno",
        "luglio","agosto","settembre","ottobre","novembre","dicembre",
    ]
    data_fmt = f"{today.day} {mesi_it[today.month - 1]} {today.year}"

    st.markdown(
        f"<h4 style='margin-bottom:4px'>📅 Bacheca del giorno — <span style='color:#4A90D9'>{data_fmt}</span></h4>"
        "<hr style='margin:6px 0 14px 0; border-color:#e5e7eb'>",
        unsafe_allow_html=True,
    )

    col_s, col_h, col_c = st.columns(3)

    # ── 1. Santo del giorno ──────────────────────────────────────────────────
    with col_s:
        nome_santo, nota_santo = _get_santo(today)
        has_campania = nome_santo.startswith("San Gennaro") or (nota_santo and "🌋" in nota_santo)
        border = "#e74c3c" if has_campania else "#8b5cf6"
        icon   = "🌋" if has_campania else "✝️"
        st.markdown(
            f"""
            <div style='border-left:4px solid {border};padding:10px 12px;
                        background:#fafafa;border-radius:6px;min-height:140px'>
              <div style='font-size:1.3rem'>{icon}</div>
              <div style='font-size:0.7rem;color:#6B7280;text-transform:uppercase;
                          letter-spacing:.05em;margin-bottom:4px'>Santo del giorno</div>
              <div style='font-weight:600;font-size:0.92rem;margin-bottom:6px'>{nome_santo}</div>
              {"<div style='font-size:0.8rem;color:#374151'>" + nota_santo + "</div>" if nota_santo else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 2. Oggi nella storia ─────────────────────────────────────────────────
    with col_h:
        eventi = _STORIA.get((today.month, today.day), [])
        if eventi:
            ev         = eventi[0]
            icona_ev   = ev.get("icona", "🕰️")
            a          = ev["anno"]
            if a < 0:
                anno_display = f"{abs(a)} a.C."
            elif a < 1000:
                anno_display = f"{a} d.C."
            else:
                anno_display = str(a)
            testo_ev = ev["testo"]
        else:
            icona_ev     = "🕰️"
            anno_display = ""
            testo_ev     = "Nessun evento sismico o vulcanico campano di rilievo registrato per questa data."
        has_evento = bool(eventi)
        border_h   = "#e74c3c" if has_evento else "#9CA3AF"
        anno_html  = (f"<div style='font-weight:600;font-size:0.92rem;margin-bottom:4px'>{anno_display}</div>"
                      if anno_display else "")
        extra_html = (f"<div style='font-size:0.75rem;color:#9CA3AF;margin-top:6px'>+ {len(eventi)-1} altri eventi oggi</div>"
                      if len(eventi) > 1 else "")
        st.markdown(
            f"""
            <div style='border-left:4px solid {border_h};padding:10px 12px;
                        background:#fafafa;border-radius:6px;min-height:140px'>
              <div style='font-size:1.3rem'>{icona_ev}</div>
              <div style='font-size:0.7rem;color:#6B7280;text-transform:uppercase;
                          letter-spacing:.05em;margin-bottom:4px'>Oggi nella storia</div>
              {anno_html}
              <div style='font-size:0.82rem;color:#374151;line-height:1.4'>{testo_ev[:220]}{"…" if len(testo_ev) > 220 else ""}</div>
              {extra_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── 3. Curiosità vulcanologica ───────────────────────────────────────────
    with col_c:
        date_key = today.strftime("%Y%m%d")
        idx_fallback = int(hashlib.md5(date_key.encode()).hexdigest(), 16) % len(_CURIOSITA_POOL)
        titolo_fb, testo_fb = _CURIOSITA_POOL[idx_fallback]

        ai_text = _get_curiosita_ai(date_key)
        titolo_show = "✨ Dall'AI" if ai_text else titolo_fb
        testo_show  = ai_text if ai_text else testo_fb

        st.markdown(
            f"""
            <div style='border-left:4px solid #f39c12;padding:10px 12px;
                        background:#fafafa;border-radius:6px;min-height:140px'>
              <div style='font-size:1.3rem'>🌋</div>
              <div style='font-size:0.7rem;color:#6B7280;text-transform:uppercase;
                          letter-spacing:.05em;margin-bottom:4px'>Curiosità vulcanologica</div>
              <div style='font-weight:600;font-size:0.85rem;margin-bottom:4px;color:#b45309'>{titolo_show}</div>
              <div style='font-size:0.82rem;color:#374151;line-height:1.4'>{testo_show[:280]}{"…" if len(testo_show) > 280 else ""}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
