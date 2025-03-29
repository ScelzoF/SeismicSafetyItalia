
import streamlit as st

def show_monitoring_page(earthquake_data, get_text):
    st.title("Monitoraggio Sismico")
    st.write("Visualizzazione dati real-time")

    # Mostriamo i dati sismici
    if earthquake_data:
        st.markdown("### Ultimi eventi sismici:")
        st.write(f"Evento: {earthquake_data['event_name']}")
        st.write(f"Magnitudo: {earthquake_data['magnitude']}")
        st.write(f"Profondità: {earthquake_data['depth']} km")
    else:
        st.write("Nessun evento sismico recente.")

    # Testo aggiuntivo da get_text
    st.markdown("### Dettagli aggiuntivi:")
    st.write(get_text())

    # Mostriamo una tabella di esempio
    st.table({"Evento": ["Sisma 1"], "Magnitudo": [4.0], "Profondità": [10]})
