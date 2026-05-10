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
    # ── GENNAIO ──────────────────────────────────────────────────────────────
    (1,  1): ("Santa Maria Madre di Dio",          "Primo giorno dell'anno — solennità mariana"),
    (1,  2): ("Santi Basilio e Gregorio",           "Due grandi teologi del IV secolo"),
    (1,  3): ("Santissimo Nome di Gesù",            None),
    (1,  4): ("Sant'Elisabetta Anna Seton",         "Prima santa nata negli USA — fondatrice delle Figlie della Carità in America"),
    (1,  5): ("San Telesforo",                      "Papa e martire del II secolo"),
    (1,  6): ("Epifania del Signore",               "I Re Magi portano doni a Gesù — festa nazionale"),
    (1,  7): ("San Raimondo de Peñafort",           None),
    (1,  8): ("San Severino di Noricum",            None),
    (1,  9): ("Sant'Adriano di Canterbury",         None),
    (1, 10): ("San Gregorio di Nissa",              None),
    (1, 11): ("Sant'Igino",                         "Papa e martire del II secolo"),
    (1, 12): ("San Modesto di Treviri",             None),
    (1, 13): ("Sant'Ilario di Poitiers",            None),
    (1, 14): ("San Felice da Nola",                 "🌋 Martire campano del III secolo — venerato a Nola, ai piedi del Vesuvio"),
    (1, 15): ("San Mauro",                          "Discepolo prediletto di San Benedetto"),
    (1, 16): ("San Marcello I",                     "Papa e martire del IV secolo"),
    (1, 17): ("Sant'Antonio Abate",                 "Patrono degli animali; in Campania si accendono i fuochi di Sant'Antonio"),
    (1, 18): ("Santa Prisca",                       "Giovane martire romana del I secolo"),
    (1, 19): ("Santi Mario e Marta",                None),
    (1, 20): ("San Sebastiano",                     "Martire romano, patrono degli atleti e della polizia"),
    (1, 21): ("Sant'Agnese",                        "Giovane martire romana del III secolo"),
    (1, 22): ("San Vincenzo di Saragozza",          "Diacono e martire, patrono dei vinaioli"),
    (1, 23): ("Sant'Emerenziana",                   "Giovane martire romana, nutrice di Sant'Agnese"),
    (1, 24): ("San Francesco di Sales",             "Patrono dei giornalisti e scrittori"),
    (1, 25): ("Conversione di San Paolo",           "L'apostolo cambia vita sulla via di Damasco"),
    (1, 26): ("Santi Timoteo e Tito",               None),
    (1, 27): ("Santa Angela Merici",                "Fondatrice delle Orsoline, patrona delle ragazze"),
    (1, 28): ("San Tommaso d'Aquino",               "Patrono degli studenti, nato a Roccasecca (FR) — Dottore della Chiesa"),
    (1, 29): ("San Costanzo di Perugia",            None),
    (1, 30): ("San Giacinto Castañeda",             None),
    (1, 31): ("San Giovanni Bosco",                 "Patrono dei giovani e degli insegnanti, fondatore dei Salesiani"),
    # ── FEBBRAIO ─────────────────────────────────────────────────────────────
    (2,  1): ("Sant'Verdiana",                      None),
    (2,  2): ("Presentazione del Signore",          "Candelora — metà dell'inverno; si benedicono le candele"),
    (2,  3): ("San Biagio",                         "Patrono dei malati di gola — si benedicono le gole con candele"),
    (2,  4): ("San Gilberto di Sempringham",        None),
    (2,  5): ("Sant'Agata",                         "Patrona di Catania — protegge dall'Etna; il velo di Agata è portato in processione attorno alla lava"),
    (2,  6): ("San Paolo Miki e compagni",          "I 26 martiri del Giappone, crocifissi a Nagasaki nel 1597"),
    (2,  7): ("San Riccardo",                       None),
    (2,  8): ("San Girolamo Emiliani",              "Fondatore dei Somaschi, patrono degli orfani e della gioventù abbandonata"),
    (2,  9): ("Santa Apollonia",                    "Martire alessandrina — patrona dei dentisti"),
    (2, 10): ("Santa Scolastica",                   "Sorella gemella di San Benedetto"),
    (2, 11): ("Beata Vergine di Lourdes",           "Le apparizioni del 1858 a Bernadette Soubirous"),
    (2, 12): ("Santa Eulalia di Barcellona",        None),
    (2, 13): ("Sant'Agabo",                         None),
    (2, 14): ("San Valentino di Terni",             "Patrono degli innamorati — il vescovo fu martirizzato nel 273 d.C."),
    (2, 15): ("Santi Faustino e Giovita",           "Martiri bresciani del II secolo — patroni di Brescia"),
    (2, 16): ("San Giuliana di Nicomedia",          None),
    (2, 17): ("Sette Fondatori dei Servi di Maria", "Sette nobili fiorentini che fondarono l'Ordine dei Servi nel 1233"),
    (2, 18): ("Beato Fra Angelico",                 "Pittore domenicano del Rinascimento, patrono degli artisti"),
    (2, 19): ("San Corrado di Piacenza",            None),
    (2, 20): ("San Francesco Regio",                None),
    (2, 21): ("San Pier Damiani",                   "Cardinale e Dottore della Chiesa, riformatore monastico dell'XI secolo"),
    (2, 22): ("Cattedra di San Pietro",             None),
    (2, 23): ("San Policarpo",                      "Vescovo di Smirne, discepolo dell'apostolo Giovanni, martire nel 155 d.C."),
    (2, 24): ("San Sergio I",                       None),
    (2, 25): ("San Cesario di Nazianzo",            None),
    (2, 26): ("Sant'Alessandra",                    None),
    (2, 27): ("San Gabriele dell'Addolorata",       "Passionista, patrono della gioventù d'Abruzzo — morì a 24 anni"),
    (2, 28): ("Sant'Romano Abate",                  None),
    (2, 29): ("San Cassio di Narni",                "Vescovo del VI secolo — il santo del giorno bisestile"),
    # ── MARZO ────────────────────────────────────────────────────────────────
    (3,  1): ("Sant'Albino di Angers",              None),
    (3,  2): ("San Simplicio",                      None),
    (3,  3): ("San Cuniberto",                      None),
    (3,  4): ("San Casimiro",                       "Patrono della Polonia e della Lituania — morì a 25 anni"),
    (3,  5): ("Sant'Adriano di Cesarea",            None),
    (3,  6): ("Santi Felicita e i suoi sette figli","Martiri romani del II secolo"),
    (3,  7): ("Sante Perpetua e Felicita",          "Martiri cartaginesi del 203 d.C."),
    (3,  8): ("San Giovanni di Dio",                "Patrono degli infermi e degli ospedali"),
    (3,  9): ("Santa Francesca Romana",             "Patrona di Roma — fondatrice delle Oblate Benedettine nel XV secolo"),
    (3, 10): ("San Macario di Gerusalemme",         None),
    (3, 11): ("San Costantino",                     None),
    (3, 12): ("San Massimiliano",                   None),
    (3, 13): ("Sant'Euprassia",                     None),
    (3, 14): ("Santa Matilde",                      "Regina di Germania nel X secolo"),
    (3, 15): ("Sant'Luisa de Marillac",             None),
    (3, 16): ("Santa Luisa de Marillac",            "Fondatrice delle Figlie della Carità con San Vincenzo de' Paoli"),
    (3, 17): ("San Patrizio",                       "Patrono dell'Irlanda — evangelizzò l'isola nel V secolo"),
    (3, 18): ("San Cirillo di Gerusalemme",         "Vescovo e Dottore della Chiesa del IV secolo"),
    (3, 19): ("San Giuseppe",                       "Sposo di Maria, patrono dei padri, dei lavoratori e dei falegnami — festa nazionale"),
    (3, 20): ("Sant'Cutberto",                      None),
    (3, 21): ("San Serapione",                      None),
    (3, 22): ("Sant'Lea di Roma",                   None),
    (3, 23): ("San Turibio de Mogrovejo",           "Arcivescovo di Lima, apostolo del Nuovo Mondo"),
    (3, 24): ("Sant'Agapito",                       None),
    (3, 25): ("Annunciazione del Signore",          "L'Angelo annuncia a Maria la nascita di Gesù — 9 mesi prima di Natale"),
    (3, 26): ("San Braganza",                       None),
    (3, 27): ("San Ruperto di Salisburgo",          None),
    (3, 28): ("Sant'Eutropio di Orange",            None),
    (3, 29): ("Sant'Bertoldo",                      None),
    (3, 30): ("Santa Margherita Clitherow",         None),
    (3, 31): ("San Beniamino",                      None),
    # ── APRILE ───────────────────────────────────────────────────────────────
    (4,  1): ("Sant'Ugo di Grenoble",               None),
    (4,  2): ("San Francesco da Paola",             "🌋 Calabrese, fondatore dei Minimi — patrono della gente di mare; molto venerato nel Sud Italia"),
    (4,  3): ("San Riccardo di Chichester",         None),
    (4,  4): ("Sant'Isidoro di Siviglia",           "Dottore della Chiesa, patrono di internet e degli informatici"),
    (4,  5): ("San Vincenzo Ferrer",                "Domenicano valenciano, grande predicatore del XV secolo"),
    (4,  6): ("Sant'Celestino I",                   None),
    (4,  7): ("San Giovanni Battista de la Salle",  "Fondatore dei Fratelli delle Scuole Cristiane, patrono degli insegnanti"),
    (4,  8): ("Sant'Alberto di Gerusalemme",        None),
    (4,  9): ("Santa Maria di Cleofa",              None),
    (4, 10): ("San Fulberto",                       None),
    (4, 11): ("San Stanislao di Cracovia",          "Vescovo e martire polacco dell'XI secolo"),
    (4, 12): ("San Giulio I",                       "Papa del IV secolo — combatté l'arianesimo"),
    (4, 13): ("San Martino I",                      "Papa e martire del VII secolo"),
    (4, 14): ("San Valeriano",                      None),
    (4, 15): ("Sant'Anastasia",                     None),
    (4, 16): ("Santa Bernadette Soubirous",         "Veggente di Lourdes — vide la Madonna 18 volte nel 1858"),
    (4, 17): ("Sant'Aniceto",                       None),
    (4, 18): ("San Galdino",                        None),
    (4, 19): ("Sant'Emma",                          None),
    (4, 20): ("Sant'Adalberto",                     None),
    (4, 21): ("Sant'Anselmo di Aosta",              "Arcivescovo di Canterbury, Dottore della Chiesa — 'Credo ut intelligam'"),
    (4, 22): ("Sant'Alessandro",                    None),
    (4, 23): ("San Giorgio",                        "Martire, patrono dell'Inghilterra, del Libano e di numerose città"),
    (4, 24): ("San Fedele da Sigmaringen",          None),
    (4, 25): ("San Marco Evangelista",              "Patrono di Venezia — festa nazionale"),
    (4, 26): ("Santa Marcellina",                   None),
    (4, 27): ("Santa Zita",                         "Patrona dei domestici e dei lavoratori — venerata a Lucca"),
    (4, 28): ("San Luigi Maria Grignion de Montfort",None),
    (4, 29): ("Santa Caterina da Siena",            "Patrona d'Italia, Dottore della Chiesa, mistica medievale"),
    (4, 30): ("San Pio V",                          "Papa dal 1566 al 1572 — promosse la Lega Santa che vinse a Lepanto (1571)"),
    # ── MAGGIO ───────────────────────────────────────────────────────────────
    (5,  1): ("San Giuseppe Lavoratore",            "Festa dei Lavoratori — festa nazionale"),
    (5,  2): ("San Atanasio",                       "Vescovo di Alessandria, Dottore della Chiesa — difese la divinità di Cristo contro l'arianesimo"),
    (5,  3): ("Santi Filippo e Giacomo",            "Due apostoli di Gesù"),
    (5,  4): ("Sant'Antonino di Sorrento",          "🌋 Patrono di Sorrento, ai piedi del Vesuvio — protegge la città dalle eruzioni"),
    (5,  5): ("San Gottardo",                       None),
    (5,  6): ("San Domenico Savio",                 "Allievo di Don Bosco, morto a 14 anni — patrono dei ragazzi"),
    (5,  7): ("San Giovanni Ante Portam Latinam",   None),
    (5,  8): ("San Vittore il Moro",                None),
    (5,  9): ("San Pacomio",                        "Fondatore del monachesimo cenobitico in Egitto"),
    (5, 10): ("San Cataldo",                         "🌋 Vescovo irlandese del VII secolo — patrono di Taranto e protettore dalle epidemie; venerato in tutto il Sud Italia"),
    (5, 11): ("San Fabio martire",                  "Martire romano del IV secolo — decapitato sotto Diocleziano per aver rifiutato di adorare gli idoli"),
    (5, 12): ("Santi Nereo e Achilleo",             None),
    (5, 13): ("Beata Vergine di Fatima",            "Le apparizioni del 1917 ai tre pastorelli in Portogallo"),
    (5, 14): ("San Mattia Apostolo",                "Eletto al posto di Giuda Iscariota tra i Dodici"),
    (5, 15): ("Sant'Isidoro Agricoltore",           "Contadino spagnolo del XII secolo — patrono dei contadini"),
    (5, 16): ("San Giovanni Nepomuceno",            "Patrono della Boemia, martire del segreto confessionale"),
    (5, 17): ("San Pasquale Baylon",                "Frate francescano, patrono dei congressi eucaristici"),
    (5, 18): ("San Giovanni I",                     "Papa e martire del VI secolo"),
    (5, 19): ("San Celestino V",                    "🌋 Papa-eremita nato a Isernia — fondò i Celestini; famoso per la 'grande rinuncia'. Molto venerato in Campania e Molise"),
    (5, 20): ("San Bernardino da Siena",            "Francescano, grande predicatore popolare del XV secolo"),
    (5, 21): ("San Cristoforo Magallanes",          None),
    (5, 22): ("Santa Rita da Cascia",               "Patrona delle cause impossibili — vita di sofferenza e misticismo"),
    (5, 23): ("San Desiderio",                      None),
    (5, 24): ("Santa Maria Ausiliatrice",           "Titolo mariano caro ai Salesiani di Don Bosco"),
    (5, 25): ("San Gregorio VII",                   "Papa riformatore dell'XI secolo — lottò per l'indipendenza della Chiesa"),
    (5, 26): ("San Filippo Neri",                   "Patrono di Roma, fondatore dell'Oratorio — 'il santo della gioia'"),
    (5, 27): ("Sant'Agostino di Canterbury",        "Primo arcivescovo di Canterbury, apostolo degli Anglosassoni"),
    (5, 28): ("Sant'Emilio di Nantes",              None),
    (5, 29): ("Sant'Urso",                          None),
    (5, 30): ("Santa Giovanna d'Arco",              "La pulzella d'Orléans — liberò la Francia, morì sul rogo a 19 anni"),
    (5, 31): ("Visitazione della Vergine Maria",    "Maria visita la cugina Elisabetta, madre di Giovanni Battista"),
    # ── GIUGNO ───────────────────────────────────────────────────────────────
    (6,  1): ("San Giustino",                       "Martire e filosofo cristiano del II secolo"),
    (6,  2): ("Santi Marcellino e Pietro",          None),
    (6,  3): ("Santi Carlo Lwanga e compagni",      "I martiri dell'Uganda — uccisi per la fede nel 1886"),
    (6,  4): ("Santa Saturnina",                    None),
    (6,  5): ("San Bonifacio",                      "Apostolo della Germania — martire nel 754 d.C."),
    (6,  6): ("San Norberto",                       "Fondatore dei Premostratensi nel XII secolo"),
    (6,  7): ("San Roberto di Molesme",             None),
    (6,  8): ("San Medardo",                        None),
    (6,  9): ("Sant'Efrem",                         "Diacono e Dottore della Chiesa siriaco del IV secolo"),
    (6, 10): ("Sant'Oliva",                         None),
    (6, 11): ("San Barnaba Apostolo",               "Compagno di San Paolo nelle missioni — levita cipriota"),
    (6, 12): ("San Giovanni da Sahagun",            None),
    (6, 13): ("Sant'Antonio di Padova",             "Uno dei santi più amati in Italia — patrono dei poveri e dei viaggiatori"),
    (6, 14): ("San Eliseo",                         None),
    (6, 15): ("San Vito",                           "🌋 Martire del III-IV secolo — molto venerato in Campania; San Vito sul Cilento porta il suo nome"),
    (6, 16): ("Sant'Aureliano",                     None),
    (6, 17): ("San Ranieri di Pisa",                "Patrono di Pisa — pellegrino e penitente del XII secolo"),
    (6, 18): ("San Gregorio Barbarigo",             None),
    (6, 19): ("San Romualdo",                       "Fondatore dei Camaldolesi — scelse il silenzio e la solitudine"),
    (6, 20): ("Sant'Ettore",                        None),
    (6, 21): ("San Luigi Gonzaga",                  "Patrono della gioventù"),
    (6, 22): ("San Tommaso Moro",                   "Cancelliere d'Inghilterra, martire sotto Enrico VIII — patrono dei politici"),
    (6, 23): ("Sant'Edilberto",                     None),
    (6, 24): ("Natività di San Giovanni Battista",  "Precursore di Cristo — antichissima festa legata al solstizio d'estate"),
    (6, 25): ("San Guglielmo da Vercelli",          "🌋 Fondatore di Montevergine (AV) — santuario mariano sul Monte Partenio, meta di pellegrinaggi campani"),
    (6, 26): ("Santi Giovanni e Paolo",             "Martiri romani del IV secolo, fratelli"),
    (6, 27): ("San Cirillo di Alessandria",         "Dottore della Chiesa, difensore della maternità divina di Maria"),
    (6, 28): ("Sant'Ireneo di Lione",               None),
    (6, 29): ("Santi Pietro e Paolo",               "Patroni di Roma — Pietro fu crocifisso sul Colle Vaticano — festa nazionale"),
    (6, 30): ("Santi Protomartiri della Chiesa Romana", "I primi cristiani martirizzati sotto Nerone nel I secolo"),
    # ── LUGLIO ───────────────────────────────────────────────────────────────
    (7,  1): ("San Teobaldo",                       None),
    (7,  2): ("Santa Maria Goretti",                None),
    (7,  3): ("San Tommaso Apostolo",               "L'apostolo che dubitò della Resurrezione"),
    (7,  4): ("Sant'Elisabetta del Portogallo",     "Regina e terziaria francescana del XIII-XIV secolo"),
    (7,  5): ("Sant'Antonio Maria Zaccaria",        "Fondatore dei Barnabiti — nacque a Cremona nel 1502"),
    (7,  6): ("Santa Maria Goretti",                "Martire della purezza — perdonò il suo assassino prima di morire, a soli 11 anni"),
    (7,  7): ("San Benedetto XI",                   None),
    (7,  8): ("Sant'Adriano III",                   None),
    (7,  9): ("Santi Agostino Zhao Rong e compagni",None),
    (7, 10): ("San Rufino",                         None),
    (7, 11): ("San Benedetto da Norcia",            "Patrono d'Europa, fondatore del monachesimo occidentale — 'Ora et labora'"),
    (7, 12): ("San Fortunato",                      None),
    (7, 13): ("San Enrico II",                      "Imperatore del Sacro Romano Impero, modello di sovrano cristiano"),
    (7, 14): ("San Camillo de Lellis",              "🌋 Fondatore dei Camilliani — patrono dei malati e del personale sanitario; la sua opera si diffuse in tutto il Sud Italia"),
    (7, 15): ("San Bonaventura da Bagnoregio",      "Ministro generale francescano, Dottore della Chiesa — 'Doctor Seraphicus'"),
    (7, 16): ("Beata Vergine del Carmelo",          "Madonna del Carmelo, venerata in tutta la Campania e nel Golfo di Napoli"),
    (7, 17): ("Sant'Alessio",                       "Eremita romano del V secolo — patrono dei mendicanti"),
    (7, 18): ("San Simone di Gerusalemme",          None),
    (7, 19): ("Sant'Arsenio il Grande",             None),
    (7, 20): ("Sant'Apollinare di Ravenna",         "Primo vescovo di Ravenna — patrono della città, martire del I secolo"),
    (7, 21): ("San Lorenzo da Brindisi",            "🌋 Cappuccino nato a Brindisi, Dottore della Chiesa — predicò in tutto il Mezzogiorno"),
    (7, 22): ("Santa Maria Maddalena",              "Prima testimone della Resurrezione, la 'apostola degli apostoli'"),
    (7, 23): ("Santa Brigida di Svezia",            "Mistica e fondatrice dei Brigidini — patrona d'Europa"),
    (7, 24): ("San Charbel Makhlouf",               "Monaco maronita libanese del XIX secolo"),
    (7, 25): ("San Giacomo Apostolo",               "Patrono della Spagna, meta del Cammino di Santiago"),
    (7, 26): ("Santi Anna e Gioacchino",            "Genitori della Madonna, nonni di Gesù"),
    (7, 27): ("San Pantaleone",                     "Medico e martire del IV secolo — patrono dei medici e di alcune città campane"),
    (7, 28): ("Sant'Innocenzo I",                   None),
    (7, 29): ("Santa Marta",                        "Sorella di Maria e Lazzaro, patrona delle massaie"),
    (7, 30): ("San Pietro Crisolo",                 None),
    (7, 31): ("Sant'Ignazio di Loyola",             "Fondatore della Compagnia di Gesù, gran difensore della Riforma Cattolica"),
    # ── AGOSTO ───────────────────────────────────────────────────────────────
    (8,  1): ("Sant'Alfonso Maria de' Liguori",     "🌋 Nato a Napoli (1696), fondatore dei Redentoristi — Dottore della Chiesa, patrono dei moralisti. Vescovo di Sant'Agata dei Goti (BN)"),
    (8,  2): ("Sant'Eusebio di Vercelli",           None),
    (8,  3): ("San Nicodemus",                      None),
    (8,  4): ("San Giovanni Maria Vianney",         "Curé d'Ars, patrono dei parroci"),
    (8,  5): ("Madonna della Neve",                 "La basilica di Santa Maria Maggiore a Roma fu edificata secondo una visione del IV secolo"),
    (8,  6): ("Trasfigurazione del Signore",        "Gesù appare trasfigurato a Pietro, Giacomo e Giovanni sul Monte Tabor"),
    (8,  7): ("San Gaetano da Thiene",              "🌋 Fondatore dei Teatini a Napoli — veneratissimo a Napoli dove morì nel 1547. Patrono dei cercatori di lavoro"),
    (8,  8): ("San Domenico di Guzmán",             "Fondatore dell'Ordine dei Predicatori (Domenicani) nel XIII secolo"),
    (8,  9): ("Santa Teresa Benedetta della Croce", "Edith Stein — filosofa ebrea convertita, morta ad Auschwitz nel 1942"),
    (8, 10): ("San Lorenzo",                        "Diacono e martire — le stelle cadenti di San Lorenzo sono associate alla sua festa"),
    (8, 11): ("Santa Chiara d'Assisi",              "Fondatrice delle Clarisse, compagna di San Francesco"),
    (8, 12): ("Santa Giovanna Francesca di Chantal",None),
    (8, 13): ("Santi Ponziano e Ippolito",          None),
    (8, 14): ("San Massimiliano Maria Kolbe",       "Francescano polacco — si offrì al posto di un padre di famiglia ad Auschwitz"),
    (8, 15): ("Assunzione di Maria",                "Ferragosto — festa nazionale; Maria viene assunta in cielo in corpo e anima"),
    (8, 16): ("San Rocco",                          "Pellegrino e taumaturgo — patrono degli appestati. Molto venerato nel Sud Italia"),
    (8, 17): ("Sant'Giacinto Odrowaz",              None),
    (8, 18): ("Sant'Elena",                         "Madre dell'imperatore Costantino — ritrovò la Croce a Gerusalemme"),
    (8, 19): ("San Giovanni Eudes",                 None),
    (8, 20): ("San Bernardo di Chiaravalle",        "Dottore della Chiesa, grande riformatore medievale"),
    (8, 21): ("San Pio X",                          "Papa dal 1903 al 1914 — 'Tutto restaurare in Cristo'"),
    (8, 22): ("Beata Vergine Maria Regina",         None),
    (8, 23): ("Santa Rosa da Lima",                 "Prima santa delle Americhe — terziaria domenicana peruviana"),
    (8, 24): ("San Bartolomeo Apostolo",
              "🌋 In questo giorno del 79 d.C. il Vesuvio eruttò seppellendo Pompei ed Ercolano — "
              "l'apostolo fu martirizzato scorticato vivo"),
    (8, 25): ("San Luigi IX",                       "Re di Francia — crociato e sovrano giusto del XIII secolo"),
    (8, 26): ("Sant'Alessandro di Brescia",         None),
    (8, 27): ("Santa Monica",                       "Madre di Sant'Agostino, modello di pazienza materna"),
    (8, 28): ("Sant'Agostino di Ippona",            "Uno dei Padri della Chiesa, filosofo cristiano d'Africa ('Il nostro cuore è inquieto finché non riposa in Te')"),
    (8, 29): ("Martirio di San Giovanni Battista",  "Il profeta fu decapitato per ordine di Erode Antipa — la testa portata su un vassoio"),
    (8, 30): ("Sant'Fantino",                       None),
    (8, 31): ("San Raimondo Nonnato",               None),
    # ── SETTEMBRE ────────────────────────────────────────────────────────────
    (9,  1): ("Sant'Egidio",                        "Eremita e taumaturgo — patrono degli storpi e dei mendicanti"),
    (9,  2): ("Sant'Elpidio",                       None),
    (9,  3): ("San Gregorio Magno",                 "Papa e Dottore della Chiesa, organizzò la liturgia gregoriana"),
    (9,  4): ("Santa Rosalia",                      "🌋 Patrona di Palermo — secondo la tradizione salvò la città dalla pestilenza del 1625. Molto invocata nel Sud Italia"),
    (9,  5): ("Madre Teresa di Calcutta",           "Fondatrice delle Missionarie della Carità — il volto della carità nel XX secolo"),
    (9,  6): ("San Bertrand de Garrigues",          None),
    (9,  7): ("Santa Regina",                       None),
    (9,  8): ("Natività della Beata Vergine Maria", None),
    (9,  9): ("San Pier Claver",                    "Gesuita colombiano — 'schiavo degli schiavi', patrono degli schiavi e dei missionari"),
    (9, 10): ("San Nicola da Tolentino",            "Agostiniano — taumaturgo e patrono delle anime del Purgatorio"),
    (9, 11): ("San Proto e Giacinto",               None),
    (9, 12): ("Santissimo Nome di Maria",           "Istituita dopo la vittoria di Vienna del 1683 contro i Turchi"),
    (9, 13): ("San Giovanni Crisostomo",            "Patriarca di Costantinopoli, Dottore della Chiesa"),
    (9, 14): ("Esaltazione della Santa Croce",      "Si venera la croce ritrovata da Sant'Elena nel IV secolo"),
    (9, 15): ("Beata Vergine Maria Addolorata",     "Si contempla il dolore di Maria ai piedi della Croce — festa cara ai Passionisti"),
    (9, 16): ("Santi Cornelio e Cipriano",          "Papa e vescovo martiri del III secolo"),
    (9, 17): ("San Roberto Bellarmino",             "Gesuita e Dottore della Chiesa — grande difensore della fede cattolica"),
    (9, 18): ("San Tommaso da Villanova",           None),
    (9, 19): ("San Gennaro",
              "🌋 Patrono di Napoli — protegge la città dal Vesuvio. Il prodigioso scioglimento del sangue avviene "
              "tre volte l'anno: il 19 settembre (anniversario del martirio), il sabato precedente la prima domenica "
              "di maggio e il 16 dicembre (eruzione del 1631). Gennaro fu decapitato a Pozzuoli nel 305 d.C., "
              "nella stessa area dei Campi Flegrei."),
    (9, 20): ("Sant'Andrea Kim Taegon",             "Primo prete nativo coreano, martire nel 1846"),
    (9, 21): ("San Matteo Evangelista",             "Patrono di Salerno, apostolo ed ex esattore delle tasse"),
    (9, 22): ("San Maurizio e compagni",            None),
    (9, 23): ("San Pio da Pietrelcina",             "🌋 Padre Pio — nato a Pietrelcina (BN), frate cappuccino con le stigmate. Uno dei santi più amati del XX secolo"),
    (9, 24): ("Beata Vergine della Mercede",        None),
    (9, 25): ("San Cleofa",                         None),
    (9, 26): ("Santi Cosma e Damiano",              "Medici e martiri siriani del III-IV secolo — patroni dei medici e dei farmacisti"),
    (9, 27): ("San Vincenzo de' Paoli",             "Fondatore dei Lazzaristi e delle Figlie della Carità — 'apostolo della carità'"),
    (9, 28): ("San Venceslao",                      "Patrono della Boemia — duca martire del X secolo"),
    (9, 29): ("Santi Michele, Gabriele e Raffaele", "I tre Arcangeli — San Michele è patrono delle Forze Armate italiane"),
    (9, 30): ("San Girolamo",                       "Traduttore della Bibbia in latino (Vulgata), dottore penitente nel deserto"),
    # ── OTTOBRE ──────────────────────────────────────────────────────────────
    (10,  1): ("Santa Teresa di Gesù Bambino",     "La 'piccola via', patrona delle missioni"),
    (10,  2): ("Santi Angeli Custodi",              "La Chiesa festeggia gli angeli che guidano e proteggono ogni persona"),
    (10,  3): ("San Geraldo di Aurillac",           None),
    (10,  4): ("San Francesco d'Assisi",            "Patrono d'Italia e degli animali — benedizione degli animali in tutta Italia"),
    (10,  5): ("San Placido e compagni",            None),
    (10,  6): ("San Bruno di Colonia",              "Fondatore dei Certosini — cercò Dio nel silenzio e nella solitudine"),
    (10,  7): ("Beata Vergine del Rosario",         "Istituita dopo la vittoria di Lepanto del 1571 — chiesta proprio da San Pio V"),
    (10,  8): ("Santa Pelagia",                     None),
    (10,  9): ("San Giovanni Leonardi",             "Fondatore dei Chierici Regolari della Madre di Dio nel XVI secolo"),
    (10, 10): ("San Francesco Borgia",              None),
    (10, 11): ("San Giovanni XXIII",               "Papa buono — convocò il Concilio Vaticano II nel 1962"),
    (10, 12): ("San Wilfrid",                       None),
    (10, 13): ("San Edoardo il Confessore",         None),
    (10, 14): ("San Callisto I",                    "Papa e martire — già schiavo, divenne papa nel III secolo"),
    (10, 15): ("Santa Teresa d'Avila",              "Mistica spagnola, Dottore della Chiesa, riformatrice dei Carmelitani"),
    (10, 16): ("Santa Margherita Maria Alacoque",   "Mistica francese del XVII secolo — le rivelazioni del Sacro Cuore"),
    (10, 17): ("Sant'Ignazio di Antiochia",         "Vescovo e martire, discepolo degli apostoli — morì sbranato dalle belve a Roma"),
    (10, 18): ("San Luca Evangelista",              "Patrono dei medici e dei pittori — scrisse anche gli Atti degli Apostoli"),
    (10, 19): ("Santi Giovanni de Brébeuf e Isacco Jogues", None),
    (10, 20): ("Sant'Irene",                        None),
    (10, 21): ("San Corrado di Parzham",            None),
    (10, 22): ("San Giovanni Paolo II",             "Papa polacco (1978–2005) — beatificato nel 2011, canonizzato nel 2014"),
    (10, 23): ("San Giovanni da Capestrano",        None),
    (10, 24): ("San Luigi Bertrand",                None),
    (10, 25): ("Santi Crispino e Crispiniano",      None),
    (10, 26): ("Sant'Evaristo",                     None),
    (10, 27): ("Santa Emmelina",                    None),
    (10, 28): ("Santi Simone e Giuda Taddeo",       "Due apostoli di Gesù"),
    (10, 29): ("Santa Ermelinda",                   None),
    (10, 30): ("Sant'Marcello il Centurione",       None),
    (10, 31): ("San Quintino",                      None),
    # ── NOVEMBRE ─────────────────────────────────────────────────────────────
    (11,  1): ("Tutti i Santi",                     "Ognissanti — si celebra la comunione di tutti i santi in paradiso — festa nazionale"),
    (11,  2): ("Commemorazione dei Defunti",        "Giorno dei Morti — si visitano i cimiteri con fiori e candele"),
    (11,  3): ("San Martino de Porres",             "Frate domenicano, primo santo mestizo delle Americhe"),
    (11,  4): ("San Carlo Borromeo",                "Arcivescovo di Milano, grande riformatore tridentino — festa nazionale fino al 1977"),
    (11,  5): ("San Zaccaria",                      "Padre di Giovanni Battista — sacerdote del Tempio di Gerusalemme"),
    (11,  6): ("San Leonardo di Noblac",            "Eremita francese del VI secolo — patrono dei prigionieri"),
    (11,  7): ("Sant'Ernesto",                      None),
    (11,  8): ("Santi Quattro Coronati",            "Quattro scalpellini martirizzati a Roma perché si rifiutarono di scolpire idoli pagani"),
    (11,  9): ("Dedicazione della Basilica Lateranense", "La cattedrale del mondo — 'madre e capo di tutte le chiese'"),
    (11, 10): ("San Leone Magno",                   "Papa e Dottore della Chiesa — fermò Attila alle porte di Roma"),
    (11, 11): ("San Martino di Tours",              "Festa dell'autunno: 'A San Martino ogni mosto diventa vino' — si aprono le botti"),
    (11, 12): ("San Giosafat Kuncewyc",             None),
    (11, 13): ("Sant'Omobono di Cremona",           "Mercante cremonese del XII secolo — patrono dei sarti e dei commercianti"),
    (11, 14): ("San Nicasio",                       None),
    (11, 15): ("Sant'Alberto Magno",                "Domenicano e Dottore della Chiesa — maestro di San Tommaso d'Aquino"),
    (11, 16): ("Santa Margherita di Scozia",        "Regina di Scozia dell'XI secolo — modello di sovrana cristiana"),
    (11, 17): ("Santa Elisabetta d'Ungheria",       "Regina che distribuì tutti i suoi beni ai poveri — terziaria francescana"),
    (11, 18): ("Dedicazione delle Basiliche dei SS. Pietro e Paolo", "Le due basiliche romane — simboli della fede apostolica"),
    (11, 19): ("Santa Matilde",                     None),
    (11, 20): ("San Felice di Valois",              None),
    (11, 21): ("Presentazione della Beata Vergine Maria", "Maria viene offerta al Tempio di Gerusalemme dai genitori"),
    (11, 22): ("Santa Cecilia",                     "Patrona dei musicisti e della musica sacra — martirizzata a Roma nel II secolo"),
    (11, 23): ("San Clemente I",
               "🌋⚠️ Il 23/11/1980 alle 19:34 il terremoto dell'Irpinia (M6.9) devastò la Campania: 2.914 vittime, "
               "280.000 sfollati — la catastrofe sismica più grave d'Italia del dopoguerra"),
    (11, 24): ("Santi Andrea Dung-Lac e compagni",  "117 martiri vietnamiti del XVIII-XIX secolo"),
    (11, 25): ("Santa Caterina d'Alessandria",      "Patrona dei filosofi e degli studenti universitari"),
    (11, 26): ("San Silvestro Gozzolini",           None),
    (11, 27): ("San Virgilio di Salisburgo",        None),
    (11, 28): ("Sant'Giacomo della Marca",          "🌋 Francescano marchigiano del XV secolo — predicò nel Mezzogiorno, sepolto a Napoli"),
    (11, 29): ("San Saturnino",                     None),
    (11, 30): ("Sant'Andrea Apostolo",              "Fratello di Pietro, patrono della Scozia e della Russia"),
    # ── DICEMBRE ─────────────────────────────────────────────────────────────
    (12,  1): ("San Eligio",                        "Orafo e vescovo del VII secolo — patrono degli orefici e dei fabbri"),
    (12,  2): ("Santa Bibiana",                     None),
    (12,  3): ("San Francesco Saverio",             "Grande missionario gesuita in Asia — 'patrono delle missioni'"),
    (12,  4): ("Santa Barbara",                     "Martire del III secolo — patrona degli artificieri e dei minatori"),
    (12,  5): ("San Saba",                          "Fondatore della Lavra omonima in Palestina — grande monaco del V-VI secolo"),
    (12,  6): ("San Nicola di Bari",                "Il vero Babbo Natale — patrono dei bambini, marinai e viaggiatori"),
    (12,  7): ("Sant'Ambrogio",                     "Patrono di Milano — la Scala apre la stagione il 7 dicembre"),
    (12,  8): ("Immacolata Concezione",             "Maria concepita senza peccato originale — processioni in tutta Italia — festa nazionale"),
    (12,  9): ("San Juan Diego",                    "L'indio azteco a cui la Madonna apparve a Guadalupe nel 1531"),
    (12, 10): ("Sant'Eulalia di Mérida",            None),
    (12, 11): ("San Damaso I",                      "Papa che incaricò San Girolamo di tradurre la Bibbia in latino"),
    (12, 12): ("Beata Vergine di Guadalupe",        "Apparsa nel 1531 in Messico, patrona delle Americhe"),
    (12, 13): ("Santa Lucia",                       "'Santa Lucia, la notte più lunga che ci sia' — antica celebrazione del solstizio invernale"),
    (12, 14): ("San Giovanni della Croce",          "Carmelitano e Dottore della Chiesa — mistico spagnolo del XVI secolo"),
    (12, 15): ("Sant'Valeriano di Abbenza",         None),
    (12, 16): ("San Gennaro (16 dicembre)",
               "🌋 Il 16/12/1631 il Vesuvio eruttò catastroficamente: 4.000 vittime, colate laviche fino al mare. "
               "Per questo San Gennaro fa il miracolo anche il 16 dicembre."),
    (12, 17): ("Sant'Olimpia",                      None),
    (12, 18): ("Sant'Graziano di Tours",            None),
    (12, 19): ("San Anastasio I",                   None),
    (12, 20): ("Sant'Ursicino",                     None),
    (12, 21): ("San Pietro Canisio",                "Gesuita e Dottore della Chiesa — apostolo della Germania nel XVI secolo"),
    (12, 22): ("Santa Francesca Saverio Cabrini",   "Prima cittadina americana canonizzata — fondò le Missionarie del Sacro Cuore"),
    (12, 23): ("San Giovanni da Kety",              None),
    (12, 24): ("Sant'Adele",                        None),
    (12, 25): ("Natale del Signore",                "Gesù nasce a Betlemme — festa nazionale"),
    (12, 26): ("Santo Stefano",                     "Primo martire cristiano, lapidato a Gerusalemme — festa nazionale"),
    (12, 27): ("San Giovanni Apostolo",             "L'apostolo amato da Gesù, autore del Vangelo e dell'Apocalisse"),
    (12, 28): ("Santi Innocenti Martiri",           "I bambini uccisi da Erode cercando il Messia"),
    (12, 29): ("San Tommaso Becket",                "Arcivescovo di Canterbury, martire per la libertà della Chiesa — ucciso nella cattedrale nel 1170"),
    (12, 30): ("San Ruggero",                       None),
    (12, 31): ("San Silvestro I",                   "Papa dal 314 al 335 — veglia di Capodanno"),
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
            max_tokens=400,
            temperature=0.7,
        )
        text = (resp.choices[0].message.content or "").strip()
        if len(text) > 40:
            return titolo_ai, text
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. AUGURI SPECIALI — 11 MAGGIO: SAN FABIO — per Fabio Scelzo, creatore
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=86_400 * 30, show_spinner=False)
def _auguri_fabio_scelzo(anno: int) -> str:
    """
    Genera un messaggio di auguri AI per Fabio Scelzo ogni 11 maggio.
    Il seed=anno garantisce una frase diversa ogni anno, mai ripetuta.
    Cita esplicitamente lui come creatore di SismoCampania e altri progetti.
    """
    try:
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        api_key  = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "replit-proxy")
        if not base_url:
            raise RuntimeError("no proxy")
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei l'anima vulcanica di SismoCampania, app italiana di monitoraggio sismico campana. "
                        "Scrivi un messaggio di auguri per l'onomastico di Fabio Scelzo, il tuo creatore. "
                        "Fabio non è solo il creatore di SismoCampania: ha sviluppato anche altri siti web e software. "
                        "Il tono è caldo, spiritoso e personale, con metafore vulcaniche campane "
                        "(Vesuvio, Campi Flegrei, Ischia, San Gennaro). "
                        "Fai riferimento esplicito al fatto che Fabio Scelzo ha creato questa app "
                        "e altri progetti digitali. "
                        "Massimo 3 frasi. Originale e mai banale. Concludi con un emoji vulcanico."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Anno {anno} — auguri onomastico per Fabio Scelzo, "
                        "creatore di SismoCampania e di altri siti e software"
                    ),
                },
            ],
            max_tokens=250,
            temperature=0.92,
            seed=anno,
        )
        testo = (resp.choices[0].message.content or "").strip()
        if len(testo) > 30:
            return testo
    except Exception:
        pass
    # Fallback pool — varia per anno se l'AI non è disponibile
    _fallback = [
        f"Buon onomastico, Fabio Scelzo! Hai creato SismoCampania e tanti altri progetti digitali con la stessa passione con cui il Vesuvio forgia la pietra lavica — dura, preziosa e indistruttibile. Che questo {anno} sia esplosivo di soddisfazioni! 🌋",
        f"Tanti auguri, Fabio Scelzo! SismoCampania monitora i vulcani grazie alla tua mente creativa, che non si è fermata qui: altri siti e software portano la tua firma. I Campi Flegrei tremano di ammirazione! 🌋",
        f"Buon San Fabio, Fabio Scelzo! Come il bradisismo alza lentamente il suolo di Pozzuoli, la tua creatività continua ad alzare il livello — da SismoCampania agli altri tuoi progetti digitali. Auguri dal tuo vulcano preferito! 🌋",
        f"Auguri, Fabio Scelzo! Hai dato vita a SismoCampania e a molti altri software con la stessa energia di un flusso piroclastico — rapido, potente, inarrestabile. Che il {anno} ti porti nuove eruzioni di genialità! 🌋",
    ]
    return _fallback[anno % len(_fallback)]


# ─────────────────────────────────────────────────────────────────────────────
# RENDER PRINCIPALE — riquadri nativi Streamlit, layout verticale, no troncature
# ─────────────────────────────────────────────────────────────────────────────

def render_bacheca(today: _date | None = None) -> None:
    """
    Bacheca del Giorno — tre riquadri colorati nativi (info / warning / success).
    Layout verticale a piena larghezza: testo mai troncato, zero HTML custom.
    """
    if today is None:
        today = _date.today()

    mesi_it = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    data_fmt = f"{today.day} {mesi_it[today.month - 1]} {today.year}"

    st.caption(f"📅 BACHECA DEL GIORNO — {data_fmt.upper()}")

    # ── 1. Santo del giorno ──────────────────────────────────────────────────
    nome_santo, nota_santo = _get_santo(today)
    has_volcano = bool(nota_santo and ("🌋" in nota_santo or "⚠️" in nota_santo))
    s_icon = "🌋" if has_volcano else "✝️"
    body_santo = (
        f"**✝️ Santo del giorno — {nome_santo}**\n\n{nota_santo}"
        if nota_santo else
        f"**✝️ Santo del giorno — {nome_santo}**\n\n"
        "_Nessuna nota specifica per questo giorno liturgico._"
    )
    st.info(body_santo, icon=s_icon)

    # ── 1b. Auguri speciali — 11 maggio: onomastico di Fabio Scelzo ─────────
    if today.month == 5 and today.day == 11:
        msg_fabio = _auguri_fabio_scelzo(today.year)
        st.info(
            f"**🎉 Auguri, Fabio Scelzo!**\n\n{msg_fabio}",
            icon="🎂",
        )

    # ── 2. Oggi nella storia ─────────────────────────────────────────────────
    eventi   = _STORIA.get((today.month, today.day), [])
    is_today = bool(eventi)

    if eventi:
        ev_main    = eventi[0]
        near_label = ""
    else:
        ev_near = _find_nearest_event(today)
        if ev_near:
            ev_main    = ev_near
            offset     = ev_near["_offset"]
            nd         = ev_near["_near_date"]
            nd_str     = f"{nd.day} {mesi_it[nd.month - 1]}"
            near_label = (
                f"⬅ {abs(offset)} giorni fa — {nd_str}"
                if offset < 0 else
                f"➡ tra {offset} giorni — {nd_str}"
            )
        else:
            ev_main    = None
            near_label = ""

    if ev_main:
        a         = ev_main["anno"]
        anno_disp = (
            f"{abs(a)} a.C." if a < 0 else
            f"{a} d.C."      if a < 1000 else
            str(a)
        )
        icona_ev  = ev_main.get("icona", "🕰️")
        cat_label = (
            "🕰️ Oggi nella storia"
            if is_today else
            f"🕰️ Anniversario vicino ({near_label})"
        )
        body_storia = f"**{cat_label} — {anno_disp}**\n\n{ev_main['testo']}"
        for ev_extra in eventi[1:]:
            a2      = ev_extra["anno"]
            anno2   = (
                f"{abs(a2)} a.C." if a2 < 0 else
                f"{a2} d.C."      if a2 < 1000 else
                str(a2)
            )
            body_storia += (
                f"\n\n---\n\n"
                f"**{ev_extra.get('icona', '🕰️')} {anno2}** — {ev_extra['testo']}"
            )
        st.warning(body_storia, icon=icona_ev)
    else:
        st.warning(
            "**🕰️ Oggi nella storia**\n\n"
            "_Nessun evento sismico o vulcanico campano di rilievo "
            "registrato per questo periodo dell'anno._",
            icon="🕰️",
        )

    # ── 3. Curiosità vulcanologica ───────────────────────────────────────────
    date_key         = today.strftime("%Y%m%d")
    idx_fb           = int(hashlib.md5(date_key.encode()).hexdigest(), 16) % len(_CURIOSITA_POOL)
    titolo_fb, testo_fb = _CURIOSITA_POOL[idx_fb]

    ai_result = _get_curiosita_ai(date_key)
    if ai_result:
        titolo_c, testo_c = ai_result
        header = f"**🌋 Curiosità vulcanologica — {titolo_c}** ✨"
    else:
        titolo_c, testo_c = titolo_fb, testo_fb
        header = f"**🌋 Curiosità vulcanologica — {titolo_c}**"

    st.success(f"{header}\n\n{testo_c}", icon="🌋")
