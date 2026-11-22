# Stato e riavvio manuale di Sismocampania

La prima correzione del contatore è già stata integrata; l'utente ha riferito
“Success” per entrambi gli script SQL e per il controllo della funzione. Non
serve rieseguire SQL per le correzioni descritte qui: sono modifiche al codice.
Il proprietario continua a gestire manualmente il riavvio Streamlit.

Le correzioni aggiuntive descritte nell'audit non sono ancora pubblicate. Finché
la relativa proposta GitHub non viene integrata, il sito online continua a
eseguire il codice precedente.

## Dopo l'integrazione del codice

1. In GitHub, verificare che la proposta sia stata integrata nel ramo di
   produzione del repository `ScelzoF/SeismicSafetyItalia`.
2. Aprire Streamlit Cloud, selezionare l'app Sismocampania e premere **Reboot**.
   Il riavvio resta manuale; non lo eseguiremo al posto tuo.
3. Attendere che l'app torni accessibile e controllare i log di avvio. Se il
   riavvio fallisce, non ripetere SQL: verificare il primo errore nei log e
   mantenere il database intatto.

## Verifiche rapide sul sito

- Aprire **Monitoraggio**: la mappa deve caricare OpenStreetMap.
- Aprire i bollettini di Campi Flegrei, Vesuvio e Ischia: ciascuna area deve
  mostrare data e stato propri; scaricare un PDF per confermare che il link
  funzioni. I percorsi ufficiali vengono scoperti dalla navigazione INGV e la
  cache può ritardare il riconoscimento di un nuovo bollettino fino a sei ore.
- Se una fonte non è raggiungibile o non è leggibile, la UI deve indicare
  “NON DISPONIBILE”/“non verificato”; non considerare quel valore come verde,
  assenza di rischio o dato aggiornato.
- Aprire **Assistente AI**: rifiutare risposte palesemente fuori tema e
  considerare ogni commento sperimentale, non un consenso o un'allerta ufficiale.
- Aprire le pagine vulcaniche: Campi Flegrei e Ischia devono rimandare alle
  pagine ufficiali INGV, senza mostrare i vecchi video non disponibili.
- Il contatore delle sessioni deve restare persistente tra i riavvii. Il totale
  misura sessioni, non persone uniche; i rerun della stessa sessione non devono
  aggiungere una nuova visita.
- Il supporto/donazione è temporaneamente disattivato in attesa di un nuovo link
  pubblico scelto dal proprietario.

## Sospensione automatica

Streamlit Community Cloud sospende un'app dopo 12 ore senza traffico; una visita
la riattiva. Il vecchio thread del codice pingava il sito `sismoold`, non
Sismocampania. L'auto-refresh nel browser opera soltanto mentre la pagina di un
visitatore è attiva e non costituisce un servizio always-on. Per disponibilità
continua serve un piano o hosting senza ibernazione; un ping nel codice non può
garantirla né sostituire tale servizio.

## Avviso sicurezza

Un commit precedente conteneva dati finanziari in chiaro. Sono stati tolti dal
codice corrente, ma restano nella cronologia Git finché questa non viene
riscritta. Considera esposti i dati, contatta subito l'emittente per bloccare o
sostituire la carta e non riutilizzarli. La riscrittura della cronologia è
un'operazione distruttiva e non verrà eseguita senza autorizzazione esplicita.
Non inserire numeri di carta, coordinate bancarie o chiavi in chat o nel
repository.
