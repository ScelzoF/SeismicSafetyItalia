"""
Bacheca del Giorno — Comunità SismoCampania
Auto-aggiornante ogni giorno alle mezzanotte.
  1. ✝️  Santo/a del giorno   — calendario liturgico italiano con note campane
  2. 🕰️  Oggi nella storia   — eventi sismici/vulcanici campani (o anniversario più vicino)
  3. 🌋  Curiosità vulcanologica — generata dall'AI (o pool di fallback)
"""

from __future__ import annotations
import os
import hashlib
import streamlit as st
from datetime import date as _date, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 1. SANTO/A DEL GIORNO
# ─────────────────────────────────────────────────────────────────────────────

_SANTI: dict[tuple[int, int], tuple[str, str | None]] = {
    # Gennaio
    (1,  1): ("Santa Maria Madre di Dio",         "Primo giorno dell'anno — solennità mariana"),
    (1,  2): ("Santi Basilio e Gregorio",          "Due grandi teologi del IV secolo"),
    (1,  3): ("Santissimo Nome di Gesù",           None),
    (1,  5): ("San Giovanni Nepomuceno",           None),
    (1,  6): ("Epifania del Signore",              "I Re Magi portano doni a Gesù — festa nazionale"),
    (1,  7): ("San Raimondo de Peñafort",          None),
    (1, 10): ("San Gregorio di Nissa",             None),
    (1, 13): ("Sant'Ilario di Poitiers",           None),
    (1, 17): ("Sant'Antonio Abate",                "Patrono degli animali; in Campania si accendono i fuochi di Sant'Antonio"),
    (1, 20): ("San Sebastiano",                    "Martire romano, patrono degli atleti e della polizia"),
    (1, 21): ("Sant'Agnese",                       "Giovane martire romana del III secolo"),
    (1, 24): ("San Francesco di Sales",            "Patrono dei giornalisti e scrittori"),
    (1, 25): ("Conversione di San Paolo",          "L'apostolo cambia vita sulla via di Damasco"),
    (1, 26): ("Santi Timoteo e Tito",              None),
    (1, 28): ("San Tommaso d'Aquino",              "Patrono degli studenti, nato a Roccasecca (FR) — Dottore della Chiesa"),
    (1, 31): ("San Giovanni Bosco",                "Patrono dei giovani e degli insegnanti, fondatore dei Salesiani"),
    # Febbraio
    (2,  2): ("Presentazione del Signore",         "Candelora — metà dell'inverno; si benedicono le candele"),
    (2,  3): ("San Biagio",                        "Patrono dei malati di gola — si benedicono le gole con candele"),
    (2,  5): ("Sant'Agata",                        "Patrona di Catania — protegge dall'Etna; il velo di Agata è portato in processione attorno alla lava"),
    (2, 10): ("Santa Scolastica",                  "Sorella gemella di San Benedetto"),
    (2, 11): ("Beata Vergine di Lourdes",          "Le apparizioni del 1858 a Bernadette Soubirous"),
    (2, 14): ("San Valentino di Terni",            "Patrono degli innamorati — il vescovo fu martirizzato nel 273 d.C."),
    (2, 22): ("Cattedra di San Pietro",            None),
    # Marzo
    (3,  7): ("Sante Perpetua e Felicita",         "Martiri cartaginesi del 203 d.C."),
    (3,  8): ("San Giovanni di Dio",               "Patrono degli infermi e degli ospedali"),
    (3, 17): ("San Patrizio",                      "Patrono dell'Irlanda — evangelizzò l'isola nel V secolo"),
    (3, 19): ("San Giuseppe",                      "Sposo di Maria, patrono dei padri, dei lavoratori e dei falegnami — festa nazionale"),
    (3, 25): ("Annunciazione del Signore",         "L'Angelo annuncia a Maria la nascita di Gesù — 9 mesi prima di Natale"),
    # Aprile
    (4,  4): ("Sant'Isidoro di Siviglia",          "Dottore della Chiesa, patrono di internet e degli informatici"),
    (4, 23): ("San Giorgio",                       "Martire, patrono dell'Inghilterra, del Libano e di numerose città"),
    (4, 24): ("San Fedele da Sigmaringen",         None),
    (4, 25): ("San Marco Evangelista",             "Patrono di Venezia — festa nazionale"),
    (4, 28): ("San Luigi Maria Grignion",          None),
    (4, 29): ("Santa Caterina da Siena",           "Patrona d'Italia, Dottore della Chiesa, mistica medievale"),
    (4, 30): ("San Pio V",                         "Papa dal 1566 al 1572 — promosse la Lega Santa che vinse a Lepanto (1571)"),
    # Maggio
    (5,  1): ("San Giuseppe Lavoratore",           "Festa dei Lavoratori — festa nazionale"),
    (5,  3): ("Santi Filippo e Giacomo",           "Due apostoli di Gesù"),
    (5,  4): ("Sant'Antonino di Sorrento",         "🌋 Patrono di Sorrento, ai piedi del Vesuvio — protegge la città dalle eruzioni"),
    (5, 12): ("Santi Nereo e Achilleo",            None),
    (5, 13): ("Beata Vergine di Fatima",           "Le apparizioni del 1917 ai tre pastorelli in Portogallo"),
    (5, 15): ("San Casimiro",                      "Patrono della Polonia e della Lituania"),
    (5, 26): ("San Filippo Neri",                  "Patrono di Roma, fondatore dell'Oratorio — 'il santo della gioia'"),
    (5, 31): ("Visitazione della Vergine Maria",   "Maria visita la cugina Elisabetta, madre di Giovanni Battista"),
    # Giugno
    (6,  2): ("Santi Marcellino e Pietro",         None),
    (6, 13): ("Sant'Antonio di Padova",            "Uno dei santi più amati in Italia — patrono dei poveri e dei viaggiatori"),
    (6, 21): ("San Luigi Gonzaga",                 "Patrono della gioventù"),
    (6, 24): ("Natività di San Giovanni Battista", "Precursore di Cristo — antichissima festa legata al solstizio d'estate"),
    (6, 28): ("Sant'Ireneo di Lione",              None),
    (6, 29): ("Santi Pietro e Paolo",              "Patroni di Roma — Pietro fu crocifisso sul Colle Vaticano — festa nazionale"),
    # Luglio
    (7,  3): ("San Tommaso Apostolo",              "L'apostolo che dubitò della Resurrezione"),
    (7, 11): ("San Benedetto da Norcia",           "Patrono d'Europa, fondatore del monachesimo occidentale — 'Ora et labora'"),
    (7, 16): ("Beata Vergine del Carmelo",         "Madonna del Carmelo, venerata in tutta la Campania e nel Golfo di Napoli"),
    (7, 22): ("Santa Maria Maddalena",             "Prima testimone della Resurrezione, la 'apostola degli apostoli'"),
    (7, 25): ("San Giacomo Apostolo",              "Patrono della Spagna, meta del Cammino di Santiago"),
    (7, 26): ("Santi Anna e Gioacchino",           "Genitori della Madonna, nonni di Gesù"),
    (7, 29): ("Santa Marta",                       "Sorella di Maria e Lazzaro, patrona delle massaie"),
    (7, 31): ("Sant'Ignazio di Loyola",            "Fondatore della Compagnia di Gesù, gran difensore della Riforma Cattolica"),
    # Agosto
    (8,  4): ("San Giovanni Maria Vianney",        "Curé d'Ars, patrono dei parroci"),
    (8,  6): ("Trasfigurazione del Signore",       "Gesù appare trasfigurato a Pietro, Giacomo e Giovanni sul Monte Tabor"),
    (8, 10): ("San Lorenzo",                       "Diacono e martire — le stelle cadenti di San Lorenzo sono associate alla sua festa"),
    (8, 11): ("Santa Chiara d'Assisi",             "Fondatrice delle Clarisse, compagna di San Francesco"),
    (8, 15): ("Assunzione di Maria",               "Ferragosto — festa nazionale; Maria viene assunta in cielo in corpo e anima"),
    (8, 20): ("San Bernardo di Chiaravalle",       "Dottore della Chiesa, grande riformatore medievale"),
    (8, 22): ("Beata Vergine Maria Regina",        None),
    (8, 24): ("San Bartolomeo Apostolo",
              "🌋 In questo giorno del 79 d.C. il Vesuvio eruttò seppellendo Pompei ed Ercolano — "
              "l'apostolo fu martirizzato scorticato vivo"),
    (8, 27): ("Santa Monica",                      "Madre di Sant'Agostino, modello di pazienza materna"),
    (8, 28): ("Sant'Agostino di Ippona",           "Uno dei Padri della Chiesa, filosofo cristiano d'Africa ('Il nostro cuore è inquieto finché non riposa in Te')"),
    # Settembre
    (9,  3): ("San Gregorio Magno",                "Papa e Dottore della Chiesa, organizzò la liturgia gregoriana"),
    (9,  8): ("Natività della Beata Vergine Maria",None),
    (9, 13): ("San Giovanni Crisostomo",           "Patriarca di Costantinopoli, Dottore della Chiesa"),
    (9, 14): ("Esaltazione della Santa Croce",     "Si venera la croce ritrovata da Sant'Elena nel IV secolo"),
    (9, 19): ("San Gennaro",
              "🌋 Patrono di Napoli — protegge la città dal Vesuvio. Il prodigioso scioglimento del sangue avviene "
              "tre volte l'anno: il 19 settembre (anniversario del martirio), il sabato precedente la prima domenica "
              "di maggio e il 16 dicembre (eruzione del 1631). Gennaro fu decapitato a Pozzuoli nel 305 d.C., "
              "nella stessa area dei Campi Flegrei."),
    (9, 21): ("San Matteo Evangelista",            "Patrono di Salerno, apostolo ed ex esattore delle tasse"),
    (9, 22): ("San Maurizio e compagni",           None),
    (9, 29): ("Santi Michele, Gabriele e Raffaele","I tre Arcangeli — San Michele è patrono delle Forze Armate italiane"),
    (9, 30): ("San Girolamo",                      "Traduttore della Bibbia in latino (Vulgata), dottore penitente nel deserto"),
    # Ottobre
    (10,  1): ("Santa Teresa di Gesù Bambino",    "La 'piccola via', patrona delle missioni"),
    (10,  4): ("San Francesco d'Assisi",           "Patrono d'Italia e degli animali — benedizione degli animali in tutta Italia"),
    (10,  7): ("Beata Vergine del Rosario",        "Istituita dopo la vittoria di Lepanto del 1571 — chiesta proprio da San Pio V"),
    (10, 15): ("Santa Teresa d'Avila",             "Mistica spagnola, Dottore della Chiesa, riformatrice dei Carmelitani"),
    (10, 18): ("San Luca Evangelista",             "Patrono dei medici e dei pittori — scrisse anche gli Atti degli Apostoli"),
    (10, 22): ("San Giovanni Paolo II",            "Papa polacco (1978–2005) — beatificato nel 2011, canonizzato nel 2014"),
    (10, 28): ("Santi Simone e Giuda Taddeo",      "Due apostoli di Gesù"),
    # Novembre
    (11,  1): ("Tutti i Santi",                    "Ognissanti — si celebra la comunione di tutti i santi in paradiso — festa nazionale"),
    (11,  2): ("Commemorazione dei Defunti",       "Giorno dei Morti — si visitano i cimiteri con fiori e candele"),
    (11,  3): ("San Martino de Porres",            "Frate domenicano, primo santo mestizo delle Americhe"),
    (11,  4): ("San Carlo Borromeo",               "Arcivescovo di Milano, grande riformatore tridentino — festa nazionale fino al 1977"),
    (11, 11): ("San Martino di Tours",             "Festa dell'autunno: 'A San Martino ogni mosto diventa vino' — si aprono le botti"),
    (11, 22): ("Santa Cecilia",                    "Patrona dei musicisti e della musica sacra — martirizzata a Roma nel II secolo"),
    (11, 23): ("San Clemente I",
               "🌋⚠️ Il 23/11/1980 alle 19:34 il terremoto dell'Irpinia (M6.9) devastò la Campania: 2.914 vittime, "
               "280.000 sfollati — la catastrofe sismica più grave d'Italia del dopoguerra"),
    (11, 25): ("Santa Caterina d'Alessandria",     "Patrona dei filosofi e degli studenti universitari"),
    (11, 30): ("Sant'Andrea Apostolo",             "Fratello di Pietro, patrono della Scozia e della Russia"),
    # Dicembre
    (12,  3): ("San Francesco Saverio",            "Grande missionario gesuita in Asia — 'patrono delle missioni'"),
    (12,  6): ("San Nicola di Bari",               "Il vero Babbo Natale — patrono dei bambini, marinai e viaggiatori"),
    (12,  7): ("Sant'Ambrogio",                    "Patrono di Milano — la Scala apre la stagione il 7 dicembre"),
    (12,  8): ("Immacolata Concezione",            "Maria concepita senza peccato originale — processioni in tutta Italia — festa nazionale"),
    (12, 12): ("Beata Vergine di Guadalupe",       "Apparsa nel 1531 in Messico, patrona delle Americhe"),
    (12, 13): ("Santa Lucia",                      "'Santa Lucia, la notte più lunga che ci sia' — antica celebrazione del solstizio invernale"),
    (12, 16): ("San Eusebio di Vercelli",
               "🌋 Il 16/12/1631 il Vesuvio eruttò catastroficamente: 4.000 vittime, colate laviche fino al mare. "
               "Per questo San Gennaro fa il miracolo anche il 16 dicembre."),
    (12, 25): ("Natale del Signore",               "Gesù nasce a Betlemme — festa nazionale"),
    (12, 26): ("Santo Stefano",                    "Primo martire cristiano, lapidato a Gerusalemme — festa nazionale"),
    (12, 27): ("San Giovanni Apostolo",            "L'apostolo amato da Gesù, autore del Vangelo e dell'Apocalisse"),
    (12, 28): ("Santi Innocenti Martiri",          "I bambini uccisi da Erode cercando il Messia"),
    (12, 31): ("San Silvestro I",                  "Papa dal 314 al 335 — veglia di Capodanno"),
}


def _get_santo(today: _date) -> tuple[str, str | None]:
    entry = _SANTI.get((today.month, today.day))
    if entry:
        return entry
    mesi = ["gennaio","febbraio","marzo","aprile","maggio","giugno",
            "luglio","agosto","settembre","ottobre","novembre","dicembre"]
    return (f"Santi e Beati del {today.day} {mesi[today.month-1]}", None)


# ─────────────────────────────────────────────────────────────────────────────
# 2. OGGI NELLA STORIA
# ─────────────────────────────────────────────────────────────────────────────

_STORIA: dict[tuple[int, int], list[dict]] = {
    (1,  5): [{"anno": 1973, "icona": "🌋",
               "testo": "Intensa crisi bradisismica ai Campi Flegrei: l'INGV OV inizia il monitoraggio "
                        "sistematico del sollevamento del suolo a Pozzuoli."}],
    (2,  4): [{"anno": 1980, "icona": "🛰️",
               "testo": "Forti scosse precursori ai Campi Flegrei. L'Osservatorio Vesuviano attiva il "
                        "monitoraggio continuo 24h della zona flegrea."}],
    (2,  5): [{"anno": 1783, "icona": "🔴",
               "testo": "Terremoto della Calabria M7.1: avvertito fortemente in tutta la Campania, "
                        "grande panico a Napoli. Serie sismica tra le più devastanti d'Italia del '700."}],
    (3, 17): [{"anno": 1944, "icona": "🌋",
               "testo": "L'ultima eruzione del Vesuvio: le colate laviche raggiungono San Sebastiano al "
                        "Vesuvio e Massa di Somma. Oltre 26 soldati alleati morti. "
                        "Da allora il Vesuvio è in quiescenza."}],
    (4,  4): [{"anno": 1906, "icona": "🌋",
               "testo": "Inizia la grande eruzione del Vesuvio (4–24 aprile): la più violenta del XX secolo. "
                        "Il pennacchio raggiunge 13 km d'altezza, cenere fino alla Calabria. 218 vittime."}],
    (4, 17): [{"anno": 1982, "icona": "⚠️",
               "testo": "Decreto governativo di sgombero parziale di Pozzuoli: circa 40.000 persone "
                        "evacuate dalla zona rossa del bradisismo. Il suolo si era sollevato di oltre 1,5 m dal 1970."}],
    (5, 16): [{"anno": 1984, "icona": "🔴",
               "testo": "Terremoto M4.2 ai Campi Flegrei durante il picco della crisi bradisismica. "
                        "Il sollevamento totale supera i 3,4 metri. Pozzuoli è quasi completamente evacuata."}],
    (6, 22): [{"anno": 1910, "icona": "🔴",
               "testo": "Terremoto di Potenza M5.8, fortemente avvertito in Campania con danni ai centri "
                        "abitati della Basilicata meridionale."}],
    (7, 26): [{"anno": 1805, "icona": "🔴",
               "testo": "Terremoto del Molise M6.6: violentissimo sisma avvertito in tutta la Campania "
                        "e in metà Italia meridionale. Oltre 5.000 vittime."}],
    (8, 21): [{"anno": 2017, "icona": "🔴",
               "testo": "Terremoto M4.0 a Casamicciola Terme, Ischia: 2 vittime, 39 feriti, ~2.600 sfollati. "
                        "Gravi danni al centro storico. L'isola è su una struttura vulcanica attiva."}],
    (8, 24): [{"anno": 79, "icona": "🌋",
               "testo": "Il Vesuvio erutta seppellendo Pompei sotto 6 m di lapilli e Ercolano sotto una "
                        "colata piroclastica. Tra 2.000 e 16.000 vittime. Plinio il Giovane la descrive "
                        "in una lettera storica. L'eruzione dura 18 ore."}],
    (9, 19): [
        {"anno": 305, "icona": "✝️",
         "testo": "Martirio di San Gennaro, vescovo di Benevento, decapitato a Pozzuoli per ordine di "
                  "Diocleziano — nell'area dei Campi Flegrei. Diventerà il patrono di Napoli."},
        {"anno": 1980, "icona": "🛰️",
         "testo": "Sciame sismico ai Campi Flegrei. I sismografi dell'INGV OV registrano una serie di "
                  "eventi M>1 in area flegrea, presagio della crisi 1982-84."},
    ],
    (9, 29): [{"anno": 1538, "icona": "🌋",
               "testo": "L'eruzione che forma Monte Nuovo nei Campi Flegrei: in soli 2 giorni nasce un "
                        "cono vulcanico alto 133 m. Preceduta da settimane di terremoti e sollevamento "
                        "del suolo. È l'ultima eruzione in area flegrea."}],
    (10,  1): [{"anno": 1983, "icona": "🔴",
                "testo": "Terremoto M4.0 ai Campi Flegrei nel pieno della crisi bradisismica 1982-84. "
                         "Le scosse diventano sempre più frequenti: oltre 1.600 eventi solo in ottobre."}],
    (11, 23): [{"anno": 1980, "icona": "🔴",
                "testo": "TERREMOTO DELL'IRPINIA: ore 19:34, M6.9. Epicentro tra Sant'Angelo dei Lombardi "
                         "e Lioni (AV). 2.914 vittime, 8.848 feriti, 280.000 sfollati. "
                         "La catastrofe sismica più grave d'Italia nel dopoguerra."}],
    (11, 26): [{"anno": 2022, "icona": "🔴",
                "testo": "Terremoto M5.9 a Casamicciola Terme (Ischia) alle ore 05:07. 12 vittime, "
                         "interi quartieri sepolti da frane. Il sisma più forte sull'isola dal 1883."}],
    (12, 16): [{"anno": 1631, "icona": "🌋",
                "testo": "La grande eruzione del Vesuvio del 1631: la più letale dal 79 d.C. Le colate "
                         "raggiungono il mare. ~4.000 vittime tra flussi piroclastici e alluvioni. "
                         "Il Vesuvio erutta poi continuamente fino al 1944."}],
    (12, 19): [{"anno": 2023, "icona": "🔴",
                "testo": "Terremoto M4.4 ai Campi Flegrei, il più forte dal 1984: ore 12:11. "
                         "Avvertito in tutta l'area napoletana. Lievi danni a edifici storici nei Comuni "
                         "della zona rossa. Accelerazione del bradisismo in corso."}],
    (12, 28): [{"anno": 1908, "icona": "🔴",
                "testo": "Terremoto di Messina M7.1: la più grave catastrofe naturale d'Italia. "
                         "Oltre 80.000 vittime. Fortemente avvertito in Campania e in tutto il Sud Italia."}],
}


def _find_nearest_event(today: _date) -> dict | None:
    """
    Se non esiste un evento per oggi, cerca il più vicino nel raggio di 90 giorni
    (prima passato, poi futuro) — così la card ha sempre contenuto.
    """
    for delta in range(1, 91):
        for offset in (-delta, delta):
            d = today + timedelta(days=offset)
            evs = _STORIA.get((d.month, d.day))
            if evs:
                ev = evs[0].copy()
                ev["_offset"] = offset
                ev["_near_date"] = d
                return ev
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. CURIOSITÀ VULCANOLOGICA — pool di fallback + AI
# ─────────────────────────────────────────────────────────────────────────────

_CURIOSITA_POOL: list[tuple[str, str]] = [
    ("Temperatura del magma vesuviano",
     "Il magma del Vesuvio può raggiungere i **1.200 °C** — per confronto l'acciaio fonde a ~1.370 °C. "
     "La lava basaltica si solidifica attorno ai 700 °C formando la caratteristica roccia nera. "
     "Durante le grandi eruzioni esplosive il materiale viene scagliato fino a 20 km d'altezza."),
    ("L'energia dell'eruzione del 79 d.C.",
     "L'eruzione del Vesuvio del 79 d.C. ha liberato energia equivalente a **100.000 bombe atomiche** "
     "in meno di 24 ore. La velocità delle correnti piroclastiche superava i 700 km/h. "
     "Ercolano fu sepolta da uno strato di 25 metri di materiale in pochi minuti."),
    ("Il bradisismo di Pozzuoli",
     "Dal 2005 ad oggi il suolo di Pozzuoli si è sollevato di oltre **160 cm**. "
     "Le colonne del Serapeo romano mostrano fori di litodomi marini fino a 7 m d'altezza: "
     "prova che in epoca romana l'area era sotto il livello del mare."),
    ("La camera magmatica dei Campi Flegrei",
     "Sotto i Campi Flegrei si trovano **due serbatoi magmatici sovrapposti**: uno a ~3 km "
     "(fonte dei terremoti del bradisismo) e uno a 7-10 km di profondità. "
     "Il volume totale stimato è di alcune decine di km³ — abbastanza da coprire la Campania."),
    ("Vesuvio e il mare nel 79 d.C.",
     "Nel 79 d.C. la linea di costa era circa **2 km più interna** di oggi. "
     "Le colate piroclastiche e il materiale piroclastico hanno letteralmente spostato la riva verso il mare. "
     "Ercolano era un porto; oggi si trova a 1,5 km dalla spiaggia."),
    ("L'Osservatorio Vesuviano: il più antico del mondo",
     "Fondato nel **1841** da Ferdinando II di Borbone, l'Osservatorio Vesuviano è il più antico "
     "istituto vulcanologico del mondo. Oggi gestisce oltre 250 stazioni di monitoraggio "
     "in Campania, operative 24/7."),
    ("Dimensioni della caldera flegrea",
     "I Campi Flegrei sono una caldera di **12 km di diametro** formata da due megaeruzioni: "
     "la Campanian Ignimbrite (39.000 anni fa — la più grande eruzione europea degli ultimi 200.000 anni) "
     "e l'Ignimbrite Neapolitana (15.000 anni fa)."),
    ("Gas e fumarole alla Solfatara",
     "Ogni giorno la Solfatara di Pozzuoli emette circa **1.500 tonnellate di CO₂** e "
     "centinaia di tonnellate di vapore acqueo e anidride solforosa. "
     "Le fumarole raggiungono i 160 °C al suolo — il flusso di gas è uno dei parametri "
     "chiave del monitoraggio INGV."),
    ("Ischia: l'isola più vulcanicamente attiva d'Italia",
     "L'ultima eruzione di Ischia risale al **1302 d.C.** (Monte Arso). "
     "Il Monte Epomeo (789 m) è un blocco di tufo sollevato dal bradisismo locale. "
     "L'attività idrotermale continua alimenta le famose acque termali dell'isola."),
    ("La rete di monitoraggio INGV in Campania",
     "L'INGV Osservatorio Vesuviano gestisce **250+ stazioni** in Campania: "
     "sismometri, GPS, clinometri, sensori gas, termocamere e webcam. "
     "I dati viaggiano in tempo reale verso il Centro di Monitoraggio di Napoli — "
     "operativo senza interruzioni 365 giorni l'anno."),
    ("Come sono morti i pompeiani",
     "Le vittime di Pompei non furono sepolte dalla lava, ma da una **pioggia di lapilli** "
     "alta 6 m seguita da nubi ardenti piroclastiche a oltre 300 °C. "
     "Il calore uccise istantaneamente: i corpi carbonizzati sono così ben conservati "
     "che possiamo vedere i volti a quasi 2.000 anni di distanza."),
    ("Il prodigio del sangue di San Gennaro",
     "La liquefazione del sangue di San Gennaro avviene **tre volte l'anno**: "
     "il 19 settembre, il primo sabato di maggio e il 16 dicembre. "
     "Se il sangue non si scioglie, per i napoletani è presagio di disgrazie. "
     "Una teoria scientifica propone che sia un fluido tixotropico."),
    ("La Zona Rossa del Vesuvio",
     "La Zona Rossa comprende **18 comuni** e oltre 800.000 abitanti — "
     "la più alta concentrazione di persone in area vulcanica ad alto rischio in Europa. "
     "Il piano di evacuazione nazionale prevede 72 ore per mettere in sicurezza tutta la popolazione."),
    ("Fulmini vulcanici",
     "Durante le grandi eruzioni si formano **fulmini vulcanici**: "
     "le particelle di cenere si caricano elettrostaticamente per attrito e generano scariche fino a 200.000 V. "
     "Documentati fin dall'antichità — Plinio il Giovane li descrisse nell'eruzione del 79 d.C."),
    ("Monte Nuovo: l'ultimo vulcano nato in Europa",
     "Nel settembre 1538 nei Campi Flegrei nacque **Monte Nuovo**: "
     "in soli 2 giorni un cono vulcanico alto 133 m. "
     "Nessun altro vulcano è nato in Europa centrale negli ultimi 500 anni. "
     "L'evento fu preceduto da anni di bradisismo e da uno sciame sismico intensissimo."),
]


@st.cache_data(ttl=86_400, show_spinner=False)
def _get_curiosita_ai(date_key: str) -> tuple[str, str] | None:
    """
    Genera curiosità via AI (Replit proxy). Ritorna (titolo, testo) o None.
    date_key = "YYYYMMDD" per seed giornaliero coerente.
    """
    argomenti = [
        ("Eruzioni storiche del Vesuvio",      "le principali eruzioni storiche del Vesuvio e i loro effetti sulle popolazioni campane"),
        ("Bradisismo dei Campi Flegrei",        "il bradisismo dei Campi Flegrei: cos'è, perché avviene e cosa monitorano gli scienziati"),
        ("Terremoti vulcanici vs tettonici",    "la differenza tra terremoti vulcanici e terremoti tettonici nella Campania"),
        ("Fumarole e gas vulcanici",            "le fumarole della Solfatara di Pozzuoli e i gas vulcanici che emettono"),
        ("Monitoraggio sismico real-time",      "come funziona il monitoraggio sismico in tempo reale dell'INGV in Campania"),
        ("Piani di evacuazione vulcanici",      "i piani di emergenza e evacuazione per i vulcani campani (Vesuvio e Campi Flegrei)"),
        ("Geologia dell'Isola d'Ischia",        "la geologia vulcanica dell'Isola d'Ischia e la sua storia eruttiva"),
        ("Onde sismiche P ed S",                "le onde sismiche P ed S: come si propagano e come vengono rilevate dai sismografi"),
        ("Supervulcani e caldere",              "i supervulcani e le caldere vulcaniche nel mondo, con particolare attenzione ai Campi Flegrei"),
        ("Plinio e l'eruzione del 79 d.C.",     "Plinio il Giovane e la sua testimonianza dell'eruzione del Vesuvio del 79 d.C."),
        ("Tufo, basalto e pomice",              "le rocce vulcaniche tipiche della Campania: tufo, basalto e pomice"),
        ("Magnitudo e scala Richter",           "cosa misura la magnitudo dei terremoti e come funzionava la vecchia scala Richter"),
        ("Flussi piroclastici",                 "i flussi piroclastici: la minaccia più letale dei vulcani esplosivi"),
        ("GPS e deformazione del suolo",        "come i sensori GPS misurano la deformazione del suolo attorno ai vulcani campani"),
        ("Rischio vulcanico in Italia",         "il rischio vulcanico italiano a confronto con i vulcani più pericolosi del mondo"),
    ]
    idx = int(hashlib.md5(date_key.encode()).hexdigest(), 16) % len(argomenti)
    titolo_ai, tema = argomenti[idx]

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
                    "Sei un vulcanologo italiano divulgativo. Scrivi una curiosità affascinante e accurata "
                    "su vulcanologia o sismologia campana. Massimo 4 frasi, tono scientifico ma accessibile. "
                    "Includi un numero o dato concreto. Concludi con qualcosa di sorprendente. "
                    "Rispondi SOLO con il testo della curiosità — niente titolo, niente elenchi puntati."
                ),
            }, {
                "role": "user",
                "content": f"Scrivi una curiosità su: {tema}",
            }],
            max_tokens=220,
            temperature=0.7,
        )
        text = (resp.choices[0].message.content or "").strip()
        if len(text) > 40:
            return titolo_ai, text
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# RENDER PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
<style>
/* ── Bacheca del Giorno — dark dashboard card ── */
.bd-wrap {
  display: flex;
  gap: 14px;
  margin-bottom: 6px;
}
.bd-card {
  flex: 1;
  min-width: 0;
  background: #131c2e;
  border: 1px solid rgba(99,130,191,0.18);
  border-radius: 16px;
  padding: 18px 18px 16px;
  box-shadow: 0 6px 28px rgba(0,0,0,0.35);
  position: relative;
  overflow: hidden;
}
.bd-card::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: 16px 16px 0 0;
}
.bd-card.c-santo::before  { background: linear-gradient(90deg,#6d28d9,#8b5cf6); }
.bd-card.c-storia::before { background: linear-gradient(90deg,#b91c1c,#ef4444); }
.bd-card.c-fact::before   { background: linear-gradient(90deg,#c2410c,#f97316); }

.bd-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}
.bd-icon-box {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}
.c-santo  .bd-icon-box { background: rgba(109,40,217,.25); }
.c-storia .bd-icon-box { background: rgba(185,28,28,.25); }
.c-fact   .bd-icon-box { background: rgba(194,65,12,.25); }

.bd-cat {
  font-size: 0.63rem;
  text-transform: uppercase;
  letter-spacing: .1em;
  font-weight: 700;
  margin-bottom: 6px;
}
.c-santo  .bd-cat { color: #a78bfa; }
.c-storia .bd-cat { color: #f87171; }
.c-fact   .bd-cat { color: #fb923c; }

.bd-title {
  font-size: 1.0rem;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.3;
  margin-bottom: 10px;
}
.bd-divider {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.07);
  margin: 0 0 10px 0;
}
.bd-text {
  font-size: 0.82rem;
  color: #94a3b8;
  line-height: 1.65;
}
.bd-pill {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 20px;
  margin-bottom: 9px;
}
.bd-pill-near  { background: rgba(99,102,241,.18); color: #a5b4fc; }
.bd-pill-ai    { background: rgba(34,197,94,.15);  color: #86efac; }
.bd-pill-multi { background: rgba(251,191,36,.12); color: #fcd34d; margin-top:8px; }
.bd-year {
  font-size: 1.7rem;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: -1px;
  line-height: 1;
  margin-bottom: 10px;
}
</style>
"""


def _card(css_class: str, icon: str, category: str,
          title: str, text: str,
          year: str = "", pill_html: str = "", multi_html: str = "") -> str:
    """
    Costruisce una singola card dark-dashboard.
    year       — se presente, sostituisce il titolo grande con un anno stile numero
    pill_html  — badge opzionale sopra il testo (near-date, AI, ecc.)
    multi_html — nota opzionale in fondo
    """
    title_block = (
        f"<div class='bd-year'>{year}</div>"
        f"<div class='bd-title' style='font-size:0.88rem;margin-bottom:8px'>{title}</div>"
        if year else
        f"<div class='bd-title'>{title}</div>"
    )
    return f"""
<div class="bd-card {css_class}">
  <div class="bd-top">
    <div>
      <div class="bd-cat">{category}</div>
      {title_block}
    </div>
    <div class="bd-icon-box">{icon}</div>
  </div>
  <hr class="bd-divider">
  {pill_html}
  <div class="bd-text">{text}</div>
  {multi_html}
</div>"""


def render_bacheca(today: _date | None = None) -> None:
    """
    Renderizza la Bacheca del Giorno nella sezione Comunità.
    Tre card: Santo, Oggi nella storia, Curiosità vulcanologica.
    """
    if today is None:
        today = _date.today()

    mesi_it = [
        "gennaio","febbraio","marzo","aprile","maggio","giugno",
        "luglio","agosto","settembre","ottobre","novembre","dicembre",
    ]
    data_fmt = f"{today.day} {mesi_it[today.month - 1]} {today.year}"

    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:0.75rem;color:#64748b;text-transform:uppercase;"
        f"letter-spacing:.08em;font-weight:600;margin:0 0 8px 0'>"
        f"📅 Bacheca del giorno &mdash; {data_fmt}</p>",
        unsafe_allow_html=True,
    )

    # ── 1. Santo del giorno ──────────────────────────────────────────────────
    nome_santo, nota_santo = _get_santo(today)
    has_volcano = bool(nota_santo and ("🌋" in nota_santo or "⚠️" in nota_santo))
    s_icon  = "🌋" if has_volcano else "✝️"
    s_text  = nota_santo if nota_santo else "Consultare il Martirologio Romano per approfondire questo giorno liturgico."
    card_santo = _card(
        css_class="c-santo",
        icon=s_icon,
        category="✝️  Santo del giorno",
        title=nome_santo,
        text=s_text,
    )

    # ── 2. Oggi nella storia ─────────────────────────────────────────────────
    eventi   = _STORIA.get((today.month, today.day), [])
    is_today = bool(eventi)
    if eventi:
        ev         = eventi[0]
        near_label = ""
    else:
        ev_near = _find_nearest_event(today)
        if ev_near:
            ev     = ev_near
            offset = ev_near["_offset"]
            nd     = ev_near["_near_date"]
            nd_str = f"{nd.day} {mesi_it[nd.month-1]}"
            near_label = (f"⬅ {abs(offset)} giorni fa — {nd_str}"
                         if offset < 0 else f"➡ tra {offset} giorni — {nd_str}")
        else:
            ev         = None
            near_label = ""

    if ev:
        a = ev["anno"]
        anno_disp = (f"{abs(a)} a.C." if a < 0 else f"{a} d.C." if a < 1000 else str(a))
        icona_ev  = ev.get("icona", "🕰️")
        testo_ev  = ev["testo"]
        pill_h    = (f"<div class='bd-pill bd-pill-near'>{near_label}</div><br>"
                     if near_label else "")
        multi_h   = (f"<div class='bd-pill bd-pill-multi'>+{len(eventi)-1} eventi in questa data</div>"
                     if len(eventi) > 1 else "")
        cat_label = "🕰️  Oggi nella storia" if is_today else "🕰️  Anniversario vicino"
        card_storia = _card(
            css_class="c-storia",
            icon=icona_ev,
            category=cat_label,
            title=testo_ev[:180] + ("…" if len(testo_ev) > 180 else ""),
            text="",
            year=anno_disp,
            pill_html=pill_h,
            multi_html=multi_h,
        )
    else:
        card_storia = _card(
            css_class="c-storia",
            icon="🕰️",
            category="🕰️  Oggi nella storia",
            title="Archivio",
            text="Nessun evento sismico o vulcanico campano registrato in quest'area del calendario.",
        )

    # ── 3. Curiosità vulcanologica ───────────────────────────────────────────
    date_key      = today.strftime("%Y%m%d")
    idx_fb        = int(hashlib.md5(date_key.encode()).hexdigest(), 16) % len(_CURIOSITA_POOL)
    titolo_fb, testo_fb = _CURIOSITA_POOL[idx_fb]

    ai_result = _get_curiosita_ai(date_key)
    if ai_result:
        titolo_c, testo_c = ai_result
        pill_ai = "<div class='bd-pill bd-pill-ai'>✨ generata dall'AI</div><br>"
    else:
        titolo_c, testo_c = titolo_fb, testo_fb
        pill_ai = ""

    card_fact = _card(
        css_class="c-fact",
        icon="🌋",
        category="🌋  Curiosità vulcanologica",
        title=titolo_c,
        text=testo_c[:340] + ("…" if len(testo_c) > 340 else ""),
        pill_html=pill_ai,
    )

    # ── Render le 3 card in un unico blocco HTML ─────────────────────────────
    st.markdown(
        f"<div class='bd-wrap'>{card_santo}{card_storia}{card_fact}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)
