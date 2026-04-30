import streamlit as st
from supabase_utils import inserisci_post, carica_post
import re
from better_profanity import profanity
from collections import defaultdict
import time
import string
from translations_lib import get_text as _gt

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
            return False, _gt("forum_msg_too_short")
        
        # Controllo ripetizione parole
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word.lower()] += 1
            if word_freq[word.lower()] > 3:
                return False, _gt("forum_msg_repeated")
        
        # Controllo punteggiatura eccessiva
        punct_count = sum(1 for c in text if c in string.punctuation)
        if punct_count / len(text) > 0.3:
            return False, _gt("forum_msg_punctuation")
            
        return True, _gt("forum_content_valid")

    def check_content(self, text, username):
        # NUOVA FUNZIONE: Usa il sistema di moderazione avanzato
        moderated_message, moderation_info = filter_message(text, username)
        
        # Se il sistema di moderazione avanzato ha bloccato il messaggio
        if moderated_message != text or moderation_info is not None:
            reason = moderation_info.get('reason', _gt("forum_content_inappropriate")) if moderation_info else _gt("forum_content_inappropriate")
            return False, reason
            
        # Controllo lunghezza
        if len(text) < 3 or len(text) > 1000:
            return False, _gt("forum_msg_invalid_length")
            
        # Controllo flood
        if not self.check_flood(username):
            return False, _gt("forum_msg_rate_limit")
            
        # Controllo spam
        for pattern in self.spam_patterns:
            if re.search(pattern, text):
                return False, _gt("forum_msg_spam")
                
        # Controllo volgarità
        if profanity.contains_profanity(text):
            return False, _gt("forum_msg_profanity")
            
        # Controllo qualità
        quality_check, quality_msg = self.check_content_quality(text)
        if not quality_check:
            return False, quality_msg
            
        # Controllo caratteri speciali
        special_chars = sum(not c.isalnum() and not c.isspace() for c in text)
        if special_chars / len(text) > 0.3:
            return False, _gt("forum_msg_special_chars")
            
        return True, _gt("forum_content_valid")

def main():
    st.title(_gt("forum_title"))
    moderator = ModeratorAI()

    tab1, tab2 = st.tabs([_gt("forum_tab_forum"), _gt("forum_tab_references")])

    with tab1:
        with st.form("nuovo_post"):
            username = st.text_input(_gt("forum_username_label"))
            contenuto = st.text_area(_gt("forum_message_label"))
            invia = st.form_submit_button(_gt("forum_send_btn"))

            if invia:
                if not username or not contenuto:
                    st.error(_gt("forum_required_error"))
                else:
                    is_valid, message = moderator.check_content(contenuto, username)
                    if not is_valid:
                        st.error(f"❌ {message}")
                    else:
                        successo, messaggio = inserisci_post(username, contenuto)
                        st.success(messaggio) if successo else st.error(messaggio)

        st.divider()
        st.subheader(_gt("forum_recent_posts_title"))

        posts, errore = carica_post()
        if errore == "timeout":
            st.warning(_gt("forum_server_slow"))
        elif errore == "connessione":
            st.warning(_gt("forum_server_unavailable"))
        elif errore:
            st.warning(f"{_gt('forum_load_error')}: {errore}")
        elif posts:
            from datetime import datetime as _dt
            for post in reversed(posts):
                raw_data = post.get('data', '')
                try:
                    data_fmt = _dt.fromisoformat(raw_data.replace('Z', '+00:00')).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    data_fmt = raw_data[:16].replace('T', ' ')
                with st.container():
                    st.markdown(f"""
                    <div style='padding: 10px; border: 1px solid #eee; border-radius: 5px; margin: 5px 0;'>
                        <strong>{post['username']}</strong> <small>({data_fmt})</small><br>
                        {post['contenuto']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info(_gt("forum_no_posts"))

    with tab2:
        st.subheader("📚 Riferimenti utili — Monitoraggio sismico Campania")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🛡️ Protezione Civile & Allerta")
            st.markdown("""
- [🔴 Protezione Civile Nazionale](https://www.protezionecivile.gov.it/)
- [🔴 Protezione Civile Campania](https://www.regione.campania.it/regione/it/tematiche/protezione-civile)
- [🟡 Piano Evacuazione Campi Flegrei (PDF)](https://www.protezionecivile.gov.it/it/approfondimento/il-piano-di-protezione-civile-per-il-rischio-vulcanico-campi-flegrei/)
- [🟡 Piano Evacuazione Vesuvio (PDF)](https://www.protezionecivile.gov.it/it/approfondimento/il-piano-di-protezione-civile-per-il-rischio-vulcanico-del-vesuvio/)
- [📞 Numero Emergenze: **112**](tel:112)
""")

            st.markdown("#### 🌍 Terremoti in tempo reale")
            st.markdown("""
- [🔵 INGV — Terremoti Italia (live)](https://terremoti.ingv.it/)
- [🔵 USGS Earthquake Hazards](https://earthquake.usgs.gov/earthquakes/map/)
- [🔵 EMSC — European Seismological Centre](https://www.emsc-csem.org/)
- [🔵 Rete Sismica Nazionale INGV](https://www.ingv.it/it/monitoraggio-e-infrastrutture/reti/rete-sismica-nazionale)
""")

            st.markdown("#### 🌋 Vulcani Campania")
            st.markdown("""
- [🟠 INGV Osservatorio Vesuviano](https://www.ingv.it/it/chi-siamo/struttura/sezioni-e-centri/sezione-di-napoli-osservatorio-vesuviano)
- [🟠 Bollettini INGV OV (ufficiali)](https://www.ov.ingv.it/ov/it/bollettini.html)
- [🟠 Webcam Vesuvio](https://www.ov.ingv.it/ov/it/webcam.html)
- [🟠 Monitoraggio Bradisismo CF](https://www.ov.ingv.it/ov/it/campi-flegrei.html)
""")

        with col2:
            st.markdown("#### 📡 Dati scientifici & GPS")
            st.markdown("""
- [📡 Nevada Geodetic Lab (GPS)](http://geodesy.unr.edu/NGLStationPages/gpsnetmap/GPSNetMap.html)
- [📡 RING — Rete GPS INGV](https://ring.gm.ingv.it/)
- [📡 GPS Stazione RITE (Pozzuoli)](http://geodesy.unr.edu/NGLStationPages/stations/RITE.sta)
- [📡 UNAVCO GPS Explorer](https://www.unavco.org/instrumentation/networks/status/nota)
""")

            st.markdown("#### 💨 Qualità dell'aria & Ambiente")
            st.markdown("""
- [🍃 ARPAC — Agenzia Regionale Campania](https://www.arpacampania.it/)
- [🍃 Open-Meteo Air Quality](https://open-meteo.com/en/docs/air-quality-api)
- [🍃 Copernicus Atmosphere Service](https://atmosphere.copernicus.eu/)
- [🌡️ Solfatara — fumarole live (INGV)](https://www.ov.ingv.it/ov/it/campi-flegrei/monitoraggio-geochimico.html)
""")

            st.markdown("#### 📖 Approfondimenti & Scienza")
            st.markdown("""
- [📘 Cos'è il Bradisismo (INGV)](https://www.ingv.it/it/quest/bradisismo)
- [📘 Scala Richter / Magnitudo](https://www.ingv.it/it/quest/magnitudo-e-intensita)
- [📘 Copernicus Emergency Management](https://emergency.copernicus.eu/)
- [📘 USGS — Seismic Hazard Maps](https://earthquake.usgs.gov/hazards/)
- [📘 GFZ German Research Centre](https://www.gfz-potsdam.de/)
""")

            st.markdown("#### 📱 App & Strumenti utili")
            st.markdown("""
- [📱 App IT-Alert (Protezione Civile)](https://www.it-alert.gov.it/)
- [📱 My INGV (app terremoti)](https://play.google.com/store/apps/details?id=it.ingv.myingv)
- [🗺️ Mappa rischio sismico Italia](https://www.protezionecivile.gov.it/it/approfondimento/rischio-sismico/)
""")

        st.info("💡 Suggerimento: per emergenze, chiama il **112**. Per informazioni ufficiali sull'allerta vulcanica, "
                "consulta sempre il sito della **Protezione Civile** o i **bollettini INGV OV**.")