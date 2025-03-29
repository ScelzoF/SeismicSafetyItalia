
import streamlit as st
from supabase_utils import inserisci_post, carica_post  # Only keep the relevant imports

# Filtro AI semplice per contenuti inappropriati
PAROLE_VIETATE = ["parolaccia", "insulto", "spam", "offesa", "bestemmia"]

def è_contenuto_accettabile(testo):
    if not testo or len(testo.strip()) < 3:
        return False
    testo_lower = testo.lower()
    for parola in PAROLE_VIETATE:
        if parola in testo_lower:
            return False
    return True

def show_report_form():
    with st.form("report_form"):
        # Add form fields inside the `with` block, properly indented
        user_name = st.text_input("Nome")
        event_details = st.text_area("Dettagli dell'anomalia o pericolo")
        submit_button = st.form_submit_button("Invia segnalazione")
        if submit_button:
            if è_contenuto_accettabile(event_details):
                st.success("Segnalazione inviata con successo")
            else:
                st.error("Contenuto inappropriato")

def main():
    st.title("Forum della Comunità")
    show_report_form()

if __name__ == "__main__":
    main()
