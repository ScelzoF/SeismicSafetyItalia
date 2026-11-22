# Audit tecnico di Sismocampania

Data: 22 novembre 2026.
Repository: `ScelzoF/SeismicSafetyItalia`.
Ambito: correzioni già integrate nel ramo principale e verifiche aggiuntive in preparazione.

## Esito

La prima correzione del contatore e dei permessi è stata integrata. Le correzioni
descritte nell'aggiornamento del 22 novembre sono ancora da integrare e richiedono
il riavvio manuale del proprietario. L'utente ha confermato l'esito “Success” dei
due script SQL; l'accesso al progetto Supabase non è disponibile per una verifica
indipendente. Vedere `RIAVVIO_STREAMLIT.md`.

Questo è un audit tecnico del codice e dei percorsi provati: non è un penetration
test completo del servizio online, una certificazione o una validazione scientifica.
Non è corretto considerare tutte le funzioni e tutti i dati “certificati”.

## Ambito ed evidenze

- Esaminati i 26 moduli Python originali alla radice, requisiti, configurazione
  Streamlit, SQL di setup e documentazione. Consultati anche gli endpoint ausiliari
  Express e lo schema database TypeScript, che non sostituiscono il backend Streamlit.
- Compilazione sintattica dei moduli Python e importazione dei moduli principali.
- Test offline delle otto voci di navigazione Streamlit e monitoraggio con un
  catalogo di eventi sintetici. Nessuna chiamata AI o scrittura di produzione.
- Test su un database PostgreSQL 17 locale eliminabile: migrazione ripetuta,
  conservazione del totale, concorrenza, retry e permessi dei ruoli pubblici.
- Letture HTTPS effettive: una tile OpenStreetMap, catalogo INGV, sito OV e pagine
  ufficiali DPC. Sono verifiche puntuali, non garanzie di disponibilità futura.
- Download e parsing reali dei tre bollettini INGV OV (22 novembre 2026), dopo
  aver individuato dinamicamente le categorie e le cartelle annuali dal sito ufficiale.
- Lettura delle pagine ufficiali Streamlit sulle regole di sospensione Community Cloud.
- L'alias `CartoDB positron` è stato riprodotto con Folium 1.0.0 e
  xyzservices 2026.9.1: genera un avviso di chiave obbligatoria e un URL con
  parametro di chiave. La versione installata sul sito reale non è stata letta.

## Problemi corretti nella proposta

| Priorità | Problema verificato | Intervento |
| --- | --- | --- |
| Alta | Il fallback locale può sovrascrivere il contatore remoto con un valore più basso | Eliminati scrittura assoluta e fallback su file; incremento atomico SQL |
| Alta | Due richieste concorrenti possono perdere visite; un retry può duplicarle | Identificatore UUID per sessione, deduplicazione transazionale e aggiornamento atomico |
| Alta | La mappa usa un alias cartografico ora soggetto a chiave | URL OpenStreetMap esplicito in tutte le mappe stradali Python, comprese emergenze e modulo storico |
| Alta | La ricerca di parole-colore su pagine generiche può produrre un'allerta errata | Parser di frasi attuali e specifiche per ciascun vulcano, su pagine DPC dedicate |
| Alta | In caso di errore vengono dichiarati livelli ufficiali fissati nel codice | Dato non verificato mostrato come “NON DISPONIBILE”, senza verde predefinito |
| Alta | Un colore di allerta genera istruzioni automatiche di evacuazione | Rimosse tempistiche, trasporto obbligatorio e ordini autonomi; rinvio alle autorità |
| Alta | Il setup community consente scritture indiscriminate tramite policy `FOR ALL` | Ruoli pubblici limitati a lettura/inserimento; niente aggiornamento/cancellazione |
| Alta | Nome e contenuto dei post entrano in HTML non escapato | Escape dei campi persistiti prima del rendering |
| Media | Verifica TLS disabilitata su errori di certificato; warning soppressi globalmente | Rimossi i due fallback non verificati; nessuna soppressione globale |
| Media | XSRF e CORS disattivati nella configurazione Streamlit | Riattivate entrambe le protezioni |
| Media | Dati sismici caricati dal disco possono essere etichettati “live” | Metadato stale e avvisi sia nella pagina sia nei badge |
| Media | Il thread “keep-alive” puntava al vecchio sito e non impediva l'ibernazione | Rimosso il ping errato; chiarito che il refresh browser vale solo con visitatori attivi |
| Media | Il moderatore del forum perde la cronologia a ogni rerun | Istanza mantenuta nella sessione; non equivale a rate limiting globale |
| Media | Moderazione OpenAI usa un'interfaccia SDK rimossa | API `client.moderations.create`; niente testo utente nei log della funzione |
| Media | I timeout multi-AI si sommano e i thread possono modificare un risultato già restituito | Budget condiviso di attesa e snapshot separato dei risultati |
| Media | La configurazione URL Supabase del forum ignora Streamlit Secrets | Lettura coerente da ambiente o Secrets |
| Media | Mappe emergenza fissate a 800 pixel | Larghezza contenitore anziché valore fisso |
| Informativa | README e file SEO contengono riferimenti non aggiornati o dimostrativi | Link app corretto, rimossi sitemap dimostrativa e lastmod fisso |

Le mappe satellite ESRI restano invariate. I servizi cartografici esterni possono
comunque cambiare condizioni e disponibilità; OpenStreetMap richiede attribuzione
e rispetto della propria tile usage policy, e non offre un servizio senza limiti.

## Aspetti aperti e miglioramenti raccomandati

### 1. Validazione scientifica e dati di emergenza — alta priorità

SISMAI assegna le classi usando conteggi giornalieri e feature che includono il
giorno stesso. La calibrazione dei pesi usa inoltre un modello già addestrato
sull'intero insieme dei dati: non costituisce una validazione predittiva esterna.
I valori non vanno interpretati come probabilità validate di un terremoto o
misure ufficiali di rischio. Sono stati aggiunti avvisi più visibili e rimossi
testi che presentavano il risultato come un comunicato scientifico ufficiale.
Non sono stati cambiati silenziosamente target e assunzioni del modello.

Servono target futuri espliciti, split temporali senza leakage, backtest per area,
metriche probabilistiche calibrate, confronto con baseline e revisione competente
prima di usare questi output per decisioni operative.

Le localizzazioni e capienze di raccolta sono dati statici senza provenienza e
data di verifica per singolo record. Non è stata confermata l'attuale validità
di ciascuna voce presso i Comuni. La proposta rimuove le capienze numeriche
non documentate dal rendering principale e aggiunge un avviso esplicito.
La verifica dei piani comunali rimane necessaria: navigazione cartografica e
itinerario di evacuazione autorizzato non sono la stessa cosa.

I valori statici conservati per compatibilità non vengono presentati come misure:
la UI mostra una metrica vulcanologica solo se il campo è stato estratto dal PDF
corrente o da una serie GNSS recente. L'audit non certifica l'accuratezza
scientifica dei riferimenti storici.

### 2. Protezione community — alta priorità

Le nuove policy impediscono modifiche/cancellazioni anonime, ma l'inserimento
pubblico rimane disponibile. La moderazione nella UI può essere aggirata da
richieste dirette al database. La cronologia per sessione non impedisce a un
utente di aprire nuove sessioni o cambiare nome.

Evoluzione consigliata: scritture tramite backend/Edge Function, validazione e
limiti persistenti sul server, autenticazione e strumenti di moderazione.
Non modificare l'identità o le regole di accesso del prodotto senza scegliere
esplicitamente come devono poter partecipare i visitatori.

### 3. AI esterne: affidabilità, privacy e nomi dei modelli

Le catene g4f/free provider possono inviare contenuti a più servizi e non offrono
le garanzie di disponibilità suggerite da commenti quali “senza limiti”.
La UI usa etichette GPT/Claude/Gemini anche quando intervengono fallback:
non è dimostrato che siano tre modelli indipendenti.

Consigliati: provider espliciti configurati, nessun fallback non dichiarato,
indicazione del provider realmente usato, consenso e informativa per contenuti
personali, budget di tempo e costo e risposta chiara di indisponibilità.
Non sono state chiamate API AI a pagamento durante l'audit.

### 4. Riproducibilità delle dipendenze

`requirements.txt` non blocca le versioni e `pyproject.toml` copre soltanto una
parte dei pacchetti. Un rebuild può quindi cambiare il comportamento senza
cambiare il codice, come dimostra il servizio cartografico.

Il test locale usa Python 3.13 e dipendenze risolte il giorno dell'audit. La
versione Python e i pacchetti effettivi del deployment non sono accessibili qui.
Non sono state imposte versioni nuove di produzione senza verificarne la
compatibilità col runtime reale: per esempio la NumPy locale richiede Python
3.12+, mentre il progetto dichiara Python 3.11+.

Prima di un congelamento completo: rilevare il runtime scelto in Streamlit,
validare un ambiente pulito uguale e generare un lock/constraints coerente.
Non copiare indiscriminatamente un freeze dell'ambiente di audit.

Sono state interrogate le GitHub Security Advisories per 237 distribuzioni
visibili nell'ambiente di verifica (incluse librerie degli strumenti, non solo
dipendenze dell'app). Sono emersi due avvisi su setuptools 80.9.0.post0:
GHSA-xmj3-9gf7-h52w (basso, installazione legacy su Windows) e
GHSA-h35f-9h28-mq5c (medio, sdist su filesystem macOS).
Non sono prove di vulnerabilità nel deployment Linux e non descrivono i pacchetti
effettivamente installati sul sito. Non è stata effettuata una scansione completa
del lock npm ausiliario.

### 5. Prestazioni e manutenzione

Ridurre i fetch e i rendering eseguiti in tab non aperti; caching per area con
chiavi e TTL espliciti; moduli più piccoli per `visualization.py` e `app.py`;
log strutturati senza contenuti utente; contatori di fallimento delle fonti.
È stato sostituito `datetime.utcnow` con UTC timezone-aware nei moduli principali.
Il warning di deprecazione su `folium_static` resta un debito di compatibilità,
ma non è stato riprodotto come crash attuale.

Per scalare il conteggio, definire una retention del registro delle sessioni e
un concetto di visita esplicito. L'attuale soluzione conta sessioni Streamlit,
non visitatori unici verificati, e conserva i token per rendere sicuri i retry.

### 6. SEO, accessibilità e UX mobile

Un file `robots.txt` o `sitemap.xml` nel repository non è automaticamente servito
da Streamlit al relativo URL HTTP. Scrivere XML con `st.code` non crea una sitemap.
Non viene quindi dichiarato risolto il posizionamento sui motori di ricerca.
Una pagina pubblica indicizzabile con metadati reali è una possibile evoluzione.

Servono prove visuali su Safari iOS per tutti i tab, focus da tastiera, contrasto,
grafici e popup. I test AppTest eseguono l'app ma non verificano pixel, Leaflet
nel browser, lettori di schermo o un dispositivo reale. Il precedente controllo
browser del sito non è stato completato e non viene spacciato per un test riuscito.

## Aggiornamento del 22 novembre 2026

### Percorsi e aggiornamento dei dati

Il percorso Ischia era obsoleto: la categoria ufficiale è cambiata e il suffisso
della cartella annuale non è stabile. Ora il codice parte dalla navigazione INGV,
scopre la categoria corretta per ciascuna area e segue il link dell'anno corrente;
la stessa risoluzione è usata sia per estrarre i dati sia per scaricare il PDF.
Anche il link al PDF viene selezionato dal testo/contesto della pagina, non da uno
slug annuale immutabile; se non è possibile identificarlo, il downloader si ferma
invece di prendere un PDF casuale.
I percorsi di Campi Flegrei e Vesuvio non dipendono più da suffissi annuali
fissati nel codice. La cache di sei ore limita il carico sul sito INGV.

Verifica effettiva: il 22 novembre sono stati trovati e scaricati i PDF ufficiali
per tutte e tre le aree; l'estrazione ha identificato Campi Flegrei 17 novembre
2026 e i bollettini mensili di Vesuvio e Ischia di ottobre 2026. I badge sono ora
indipendenti per area: il successo di una fonte non può più far apparire
“aggiornate” le altre. Se una pagina o un PDF non è verificabile, il dato viene
segnalato come non disponibile/non verificato.

Le API sismiche (INGV, USGS, EMSC e GOSSIP-OV) hanno endpoint distinti, retry e
fallback su dati precedenti; Open-Meteo, NOAA, UNR e le altre API hanno formati
propri. Non esiste una riparazione universale in grado di dedurre in sicurezza
una nuova API o interpretare un formato cambiato. L'auto-risoluzione copre le
directory INGV che pubblicano i propri link; per API con schema cambiato o fonte
offline, la regola resta mostrare un fallback datato o “non disponibile”, non
inventare dati. L'app non riscrive né pubblica codice da sola.

### Provenienza delle metriche GPS e dei bollettini

Il percorso NGL della stazione RITE restituiva 404; Campi Flegrei usa ora il tasso
mensile estratto dal bollettino settimanale corrente. La stazione Ischia NAPL
restituiva dati fermi al 2024: il parser li rifiuta se superano 90 giorni. Le
metriche GPS Vesuvio/Ischia non dichiarano più “live” tassi predefiniti che il PDF
non contiene; restano non disponibili finché non arriva una misura attuale.
Le serie mensili sintetiche GNSS sono state rimosse. Il grafico storico dei
Campi Flegrei è esplicitamente di contesto e termina con il riferimento 2024.

Verifica diretta dei PDF ufficiali il 22 novembre: Vesuvio ottobre 2026 (92 eventi,
Mdmax estratto); Ischia ottobre 2026 (0 eventi nel mese, 2 negli ultimi 12 mesi);
Campi Flegrei 17 novembre 2026 (10 mm/mese dal bollettino). Questi numeri descrivono
i PDF scaricati durante la verifica, non un impegno di aggiornamento istantaneo.

### Altri problemi riprodotti dagli screenshot

- **Ibernazione Streamlit:** il worker locale pingava `sismoold.streamlit.app`,
  cioè un sito diverso; l'auto-refresh del browser funziona solo mentre una scheda
  è attiva. Non c'è un cron esterno nel repository. Streamlit Community Cloud
  sospende le app senza traffico per 12 ore; nessun ping nel codice garantisce
  disponibilità continua. Per “sempre online” serve un piano/hosting senza
  ibernazione; non viene aggiunto un ping per aggirare questa regola.
- **Multi-AI fuori tema:** fallback non dichiarati potevano riutilizzare risposte
  GPT/g4f al posto dei provider indicati e non c'era controllo di pertinenza.
  Il confronto ora accetta solo risposte pertinenti dei provider configurati,
  rifiuta testo generico come l'avviso Copilot nello screenshot, escapa il
  contenuto HTML e non chiama “consenso scientifico” l'accordo fra modelli.
  Questo non certifica le conclusioni AI; l'assistente generale mantiene ancora
  alcuni fallback esterni ed è un punto residuo di privacy/affidabilità.
- **Video non disponibile:** rimossi gli embed fissi CF e Ischia che non erano
  più accessibili; al loro posto ci sono le pagine ufficiali INGV. Il feed di
  notizie resta un percorso separato.
- **Supporto/donazioni:** rimossi dal codice corrente i metodi non più validi.
  La UI resta temporaneamente disattivata finché non viene indicato un nuovo
  collegamento pubblico; non inserire numeri di carta o coordinate bancarie nel
  repository. Dati finanziari erano presenti in un commit precedente: eliminarli
  dal file attuale non li rimuove dalla cronologia Git. La carta va sostituita/
  bloccata e la riscrittura della cronologia richiede un'autorizzazione separata.

Queste correzioni aggiuntive non sono ancora nel sito pubblicato. Un test locale
non prova che Streamlit abbia scaricato la nuova versione: il proprietario deve
integrare la proposta, riavviare e controllare i log.

## Test e limiti di rilascio

Ultima esecuzione locale: **55 test superati, 5 saltati**, inclusi i controlli su
incrementi concorrenti
con token distinti, 40 retry concorrenti dello stesso token, conservazione del
totale esistente, blocco dei reset anonimi, navigazione offline nelle otto pagine,
catalogo sintetico, risoluzione dei percorsi INGV, filtri Multi-AI e gestione
dell'allerta ignota, provenienza delle metriche GPS e conteggio Ischia a zero.
I cinque test database sono saltati perché in questa esecuzione non era configurato
un database locale eliminabile; non è stato usato Supabase. Gli 11 warning sono
principalmente deprecazioni di `folium_static` e del runtime di test: non vengono
nascosti come se fossero stati corretti tutti.

Eseguire dalla radice:

```sh
python -m pytest tests -q
```

Le prove SQL richiedono `requirements-test.txt` e `TEST_DATABASE_URL` verso un
database eliminabile chiamato `seismic_test` su localhost. I test rifiutano
esplicitamente database con altri nomi o host. Mai usare credenziali Supabase.

Non sono stati letti log o impostazioni del deployment Streamlit, non sono state
modificate policy reali Supabase e non è stato verificato il contatore reale
dopo un riavvio. La conferma online potrà avvenire soltanto dopo il rilascio manuale.
