def show():
    import streamlit as st

    st.title("🌋 Monitoraggio dei Vulcani Attivi in Italia")
    st.markdown("Visualizza lo stato attuale e le informazioni salienti dei principali vulcani italiani, con link alle fonti ufficiali e mappe interattive in arrivo.")

    st.subheader("🌋 Vesuvio")
    st.markdown("""
**Descrizione**: Uno dei vulcani più iconici del mondo. Attualmente quiescente, ma fortemente monitorato.
- **Stato attuale**: [INGV - Vesuvio](https://www.ov.ingv.it/index.php/stato-attuale)
- **Ultima eruzione**: 1944
- **Fenomeni**: sismicità, sollevamento, degassamento
    """)

    st.subheader("🌋 Campi Flegrei")
    st.markdown("""
**Descrizione**: Caldera attiva vicino Napoli, soggetta a bradisismo e attività sismica frequente.
- **Stato attuale**: [INGV - Campi Flegrei](https://www.ov.ingv.it/index.php/flegrei-stato-attuale)
- **Ultima eruzione**: 1538
- **Fenomeni**: sollevamento, gas, terremoti
    """)

    st.subheader("🌋 Ischia (vulcano)")
    st.markdown("""
**Descrizione**: Vulcano attivo con sollevamento, microsismicità e manifestazioni termali.
- **Stato attuale**: [INGV - Ischia](https://www.ov.ingv.it/index.php/ischia-stato-attuale)
- **Ultima eruzione**: 1302
- **Fenomeni**: fumarole, idrotermalismo
    """)

    st.subheader("🌋 Etna")
    st.markdown("""
**Descrizione**: Il vulcano più attivo d’Europa, protagonista di eruzioni effusive ed esplosive regolari.
- **Monitoraggio**: [INGV - Tremore vulcanico Etna](https://www.ct.ingv.it/index.php/monitoraggio-e-sorveglianza/segnali-in-tempo-reale/tremore-vulcanico)
- **Fenomeni**: lava, tremore, cenere
    """)

    st.subheader("🌋 Stromboli")
    st.markdown("""
**Descrizione**: Eruzioni continue da secoli, tra i vulcani più studiati al mondo.
- **Monitoraggio**: [INGV - Stromboli](https://www.ov.ingv.it/index.php/ricrcanew/stromboli)
- **Fenomeni**: esplosioni stromboliane, frane
    """)

    st.subheader("🌋 Vulcano (isola)")
    st.markdown("""
**Descrizione**: In crisi gassosa dal 2021. Attività fumarolica intensa e area sotto monitoraggio speciale.
- **Monitoraggio**: [Protezione Civile - Vulcano](https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vulcano/#:~:text=Su%20Vulcano%20%C3%A8%20attivo%20un,con%20telecamere%20ottiche%20e%20termiche.)
- **Fenomeni**: gas, fumarole, riscaldamento suolo
    """)

    st.subheader("🌋 Pantelleria")
    st.markdown("""
**Descrizione**: Vulcano potenzialmente attivo, geotermicamente monitorato ma inattivo da millenni.
- **Info**: [Protezione Civile - Pantelleria](https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/pantelleria/#:~:text=Le%20strutture%20preposte%20al%20monitoraggio,e%20delle%20deformazioni%20del%20suolo.)
- **Fenomeni**: fumarole, sollevamento
    """)

    st.subheader("🌋 Isola Ferdinandea")
    st.markdown("""
**Descrizione**: Vulcano sottomarino attivo emerso nel 1831. Oggi sommerso a circa 8 metri.
- **Info storica**: [Wikipedia - Ferdinandea](https://it.wikipedia.org/wiki/Isola_Ferdinandea)
- **Fenomeni**: sottomarini, rischio riemersione
    """)

    st.subheader("🌋 Marsili")
    st.markdown("""
**Descrizione**: Il più grande vulcano sottomarino d’Europa, situato nel Tirreno Meridionale.
- **Stato**: attivo ma non eruttivo in tempi recenti
- **Fenomeni**: sismicità, possibili idrotermalismi
- **Info**: [Wikipedia - Marsili](https://it.wikipedia.org/wiki/Marsili_(vulcano))
    """)