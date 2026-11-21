# Sicurezza

Il progetto è un servizio informativo indipendente: non è un sistema ufficiale
di allerta o di protezione civile. Gli scenari statistici e le risposte AI non
devono determinare decisioni di evacuazione o sostituire INGV, Protezione Civile
e disposizioni comunali.

## Segnalazioni

Per difetti non sensibili aprire un'issue nel repository, indicando passaggi di
riproduzione e comportamento atteso. Per vulnerabilità sfruttabili contattare
privatamente il manutentore; usare la segnalazione privata GitHub se abilitata.
Non pubblicare credenziali, token, dati personali, dump del database o dettagli
che consentano di danneggiare il servizio.

## Configurazione

- Conservare le credenziali solo in Streamlit Secrets o variabili d'ambiente.
- Non esporre chiavi con privilegi amministrativi nel browser.
- Mantenere abilitate verifica TLS, protezione XSRF e CORS.
- Applicare e verificare le migrazioni SQL prima del rilascio applicativo.
- Non trasformare un errore di rete in un valore rassicurante o in un azzeramento.

L'audit tecnico e i limiti della verifica sono descritti in `docs/AUDIT.md`.
Non viene dichiarata una certificazione di sicurezza o validazione scientifica.
