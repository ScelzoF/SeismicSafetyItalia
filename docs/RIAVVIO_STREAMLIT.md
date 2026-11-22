# Aggiornamento e riavvio manuale di Sismocampania

Il sito online e il database di produzione NON sono stati modificati durante
questa verifica. Le modifiche al codice sono proposte in un ramo separato.
Il riavvio da Streamlit resta manuale, a cura del proprietario.

## Prima di integrare il codice

1. Conservare un backup del database e annotare il totale attualmente confermato
   nella riga `public.visit_stats` con `id = 1`, se la tabella esiste.
   Un numero già perduto non può essere ricostruito dal nuovo codice.
2. Fermare temporaneamente la vecchia app da Streamlit, per evitare che vecchi
   processi continuino a riscrivere valori assoluti durante l'aggiornamento.
3. Nel SQL Editor del progetto Supabase corretto, eseguire
   `sql/visit_counter.sql`. Lo script conserva il totale esistente e può essere
   ripetuto. Non sostituisce un totale esistente con zero.
4. Se le tabelle community esistono, eseguire `sql/community_permissions.sql`.
   Per una nuova installazione usare prima `SUPABASE_SETUP.sql`.
   Entrambi gli script lasciano invariati i messaggi esistenti.
5. Verificare nel database che la funzione `public.register_visit(UUID)` esista
   e che la riga del contatore abbia mantenuto il totale annotato.
   Le migrazioni sono state testate su PostgreSQL locale, non sul progetto reale:
   se uno script segnala un errore, non proseguire senza controllarlo.

Non è disponibile in questa conversazione un'integrazione Supabase: gli script
non sono stati eseguiti sul database reale. Non incollare chiavi o password in chat.

## Pubblicazione e riavvio

1. Verificare in Streamlit la configurazione del repository:
   `ScelzoF/SeismicSafetyItalia`, ramo di produzione e file di avvio `app.py`.
   La configurazione effettivamente pubblicata non è stata ispezionata.
2. Controllare che `SUPABASE_URL` e `SUPABASE_KEY` siano configurate in
   Streamlit Secrets oppure nell'ambiente. Non cambiare credenziali funzionanti
   solo per questo aggiornamento.
3. Integrare la proposta GitHub solo dopo l'aggiornamento SQL.
   Streamlit può rilevare automaticamente una modifica al ramo collegato:
   l'approvazione della proposta non va quindi anticipata rispetto al database.
4. Riavviare manualmente da Streamlit e controllare i log di avvio.
   Non è stato modificato il file di avvio e non sono state aggiunte dipendenze
   di produzione. `requirements-test.txt` serve soltanto ai test.

## Controlli subito dopo il riavvio

- Aprire la pagina di monitoraggio: lo sfondo stradale deve mostrare OpenStreetMap,
  non un messaggio di richiesta chiave. Controllare anche le mappe di emergenza.
- Verificare il conteggio visite: deve partire dal totale conservato nel database.
  I rerun della stessa sessione non devono aggiungere visite; una nuova sessione
  ne aggiunge una. È un conteggio di sessioni, non di persone uniche.
- Se il database non risponde, deve comparire “temporaneamente non disponibili”.
  Non deve essere mostrato uno zero sostitutivo.
- Verificare tutte le voci del menu, anche da iPhone, e la selezione dell'area
  nella pagina emergenza. Non sono stati eseguiti test su un iPhone fisico.
- Confrontare i livelli di allerta con le pagine ufficiali della Protezione Civile.
  “NON DISPONIBILE” indica un dato non verificato, non un livello verde.

## Se il contatore non torna disponibile

Controllare configurazione, esito della migrazione e accesso alla funzione RPC.
Non ripristinare il vecchio meccanismo che copia un file locale sul totale remoto.
Una richiesta scaduta può essere già stata registrata: il nuovo identificatore
di sessione rende sicuro il tentativo successivo.

Il rollback del codice alla vecchia versione del contatore non è sicuro:
può reintrodurre gli azzeramenti. Non rimuovere le protezioni database per far
funzionare una versione precedente. In caso di errore, fermare l'app e correggere
la configurazione mantenendo intatto il totale persistente.
