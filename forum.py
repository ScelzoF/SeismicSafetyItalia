import streamlit as st
from supabase_utils import inserisci_post, carica_post
import re
from better_profanity import profanity
from collections import defaultdict
import time
import string

# Importiamo la funzione di moderazione avanzata
from chat_pubblica import filter_message

class ModeratorAI:
    def __init__(self):
        self.spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            r'(.)\1{4,}',  # Caratteri ripetuti
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'(?:\+\d{1,3})?[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Numeri di telefono
            r'\b(?:viagra|cialis|\\$\\$\\$|money|soldi facili|\.ru|\.cn)\b',  # Spam comuni
            r'(?i)(?:whatsapp|telegram|signal)\s*[+]?[0-9]+',  # Contatti messaging
        ]
        self.user_history = defaultdict(list)
        self.flood_threshold = 5  # max post in 5 minuti
        self.flood_window = 300  # 5 minuti in secondi
        profanity.load_censor_words()
        
    def check_flood(self, username):
        current_time = time.time()
        # Rimuovi post vecchi
        self.user_history[username] = [t for t in self.user_history[username] 
                                     if current_time - t < self.flood_window]
        # Aggiungi nuovo post
        self.user_history[username].append(current_time)
        return len(self.user_history[username]) <= self.flood_threshold

    def check_content_quality(self, text):
        # Controllo qualità base del testo
        words = text.split()
        if len(words) < 2:
            return False, "Il messaggio è troppo corto"
        
        # Controllo ripetizione parole
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word.lower()] += 1
            if word_freq[word.lower()] > 3:
                return False, "Troppe ripetizioni della stessa parola"
        
        # Controllo punteggiatura eccessiva
        punct_count = sum(1 for c in text if c in string.punctuation)
        if punct_count / len(text) > 0.3:
            return False, "Troppa punteggiatura"
            
        return True, "Contenuto valido"

    def check_content(self, text, username):
        # NUOVA FUNZIONE: Usa il sistema di moderazione avanzato
        moderated_message, moderation_info = filter_message(text, username)
        
        # Se il sistema di moderazione avanzato ha bloccato il messaggio
        if moderated_message != text or moderation_info is not None:
            reason = moderation_info.get('reason', 'Contenuto non appropriato') if moderation_info else "Contenuto non appropriato"
            return False, reason
            
        # Controllo lunghezza
        if len(text) < 3 or len(text) > 1000:
            return False, "Lunghezza del testo non valida (min 3, max 1000 caratteri)"
            
        # Controllo flood
        if not self.check_flood(username):
            return False, "Stai pubblicando troppi messaggi. Attendi qualche minuto."
            
        # Controllo spam
        for pattern in self.spam_patterns:
            if re.search(pattern, text):
                return False, "Contenuto non permesso (spam/link/contatti)"
                
        # Controllo volgarità
        if profanity.contains_profanity(text):
            return False, "Il contenuto contiene parole non appropriate"
            
        # Controllo qualità
        quality_check, quality_msg = self.check_content_quality(text)
        if not quality_check:
            return False, quality_msg
            
        # Controllo caratteri speciali
        special_chars = sum(not c.isalnum() and not c.isspace() for c in text)
        if special_chars / len(text) > 0.3:
            return False, "Troppi caratteri speciali"
            
        return True, "Contenuto valido"

def main():
    st.title("🗣️ Forum della Comunità")
    moderator = ModeratorAI()

    tab1, tab2 = st.tabs(["📢 Forum", "🔗 Riferimenti"])

    with tab1:
        with st.form("nuovo_post"):
            username = st.text_input("👤 Il tuo nome")
            contenuto = st.text_area("💬 Scrivi qualcosa")
            invia = st.form_submit_button("✉️ Invia")

            if invia:
                if not username or not contenuto:
                    st.error("❌ Username e contenuto sono richiesti")
                else:
                    is_valid, message = moderator.check_content(contenuto, username)
                    if not is_valid:
                        st.error(f"❌ {message}")
                    else:
                        successo, messaggio = inserisci_post(username, contenuto)
                        st.success(messaggio) if successo else st.error(messaggio)

        st.divider()
        st.subheader("📚 Post recenti")

        posts = carica_post()
        if posts:
            for post in reversed(posts):
                with st.container():
                    st.markdown(f"""
                    <div style='padding: 10px; border: 1px solid #eee; border-radius: 5px; margin: 5px 0;'>
                        <strong>{post['username']}</strong> <small>({post.get('data', '')[:16]})</small><br>
                        {post['contenuto']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Nessun post disponibile.")

    with tab2:
        st.subheader("📎 Riferimenti utili")
        st.markdown("""
        - [Protezione Civile](https://www.protezionecivile.gov.it/)
        - [INGV](https://www.ingv.it/)
        - [Copernicus EMS](https://emergency.copernicus.eu/)
        """)