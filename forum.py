
import streamlit as st
from supabase_utils import inserisci_post, carica_post, inserisci_segnalazione, carica_segnalazioni

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

def main():
    st.title("Forum della Comunità")
    
    # Placeholder for other code here

    # Example usage of inserisci_post or other functions
    if st.button("Carica post"):
        # Call inserisci_post or other functions as needed
        pass

if __name__ == "__main__":
    main()
