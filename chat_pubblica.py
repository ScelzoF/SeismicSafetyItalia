import logging
import re
import time
import hashlib
import urllib.parse
from datetime import datetime
from better_profanity import profanity
import string
from collections import defaultdict
import requests
import os
import openai
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Configura OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurazione avanzata del sistema di logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("moderazione_contenuti")

# Lista completa ed estesa di parole offensive in italiano 
blacklist_words_it = [
    # Offese comuni
    "stronzo", "stronza", "stronzi", "stronze", "str0nzo", "str0nz0", "str0nza", 
    "cazzo", "cazzi", "cazzata", "cazzate", "cazz0", "cazz0ne", "c4zzo", "c4zz0",
    "merda", "merde", "m3rda", "m3rd4", "di merda", "merdoso", "merdosa",
    "schifo", "schifoso", "schifosa", "fa schifo", "schifezza",
    "idiota", "idioti", "1d10ta", "id1ota", "1di0ta",
    "cretino", "cretini", "cret1no", "cret1n0", "cretinata",
    "puttana", "puttane", "putt4n4", "putt4na", "puttan4", "puttaniere",
    "bastardo", "bastardi", "bastarda", "bastarde", "bastar*",
    "vaffanculo", "vaffancul0", "vaffa", "vaff4", "v4ff4nculo", "vaffancul*",
    "porco", "porci", "porca", "porche", "pork0", "p0rc0",
    "stupido", "stupidi", "stupida", "stupide", "stup1do", "stup1d0",
    "testa di cazzo", "teste di cazzo", "test4 d1 cazz0",
    "frocio", "froci", "fr0ci0", "fr0c10", "frocetto", "finocchio", "checca",
    "culattone", "culattoni", "cul4tt0ne", "ricchione", "ricchioni",
    "troia", "troie", "tr01a", "tr0ia", "tr0i4", "troietta",
    "figa", "fighe", "f1ga", "f1g4", "figa di merda", "fregna",
    "figlio di puttana", "figli di puttana", "f1gl10 d1 puttan4",
    "testa di merda", "teste di merda", "t3st4 d1 m3rd4",
    "minchia", "m1nch1a", "minch14", "cazzone", "cazz0ne", "c4zzone",
    "coglione", "coglioni", "c0gl10ne", "c0gl10n1", "cogl1one", "coglio*",
    "cappella", "capp3ll4", "capp3lla", "cappelle",
    "rompicoglioni", "rompipalle", "romp1c0gl10n1", "rompicogl*",
    "imbecille", "imbecilli", "1mbec1lle", "1mbec1ll1", "imbec*",
    "deficiente", "deficienti", "def1c1ente", "def1c1ent1", "defic*",
    "mentecatto", "mentecatti", "ment3c4tt0", "ment3catt0", "mentec*",
    "ritardato", "ritardati", "r1tard4t0", "r1tardato", "ritard*",
    "stroncare", "stroncato", "str0ncare", "str0ncat0", "stronc*",
    "scemo", "scemi", "scem0", "scem1", "scemo di merda",
    "negro", "negri", "negra", "negre", "n3gr0", "n3gri", "negr*",
    "terrone", "terroni", "terr0ne", "terr0n1", "terr*",
    "polentone", "polentoni", "p0lent0ne", "p0lent0n1", "polent*",
    "zingaro", "zingari", "zingara", "zingare", "z1ngar0", "zing*",
    "pezzente", "pezzenti", "pezz3nt3", "pezz3nt1", "pezze*",
    "disgraziato", "disgraziata", "disgraziati", "disgraz1at0", "disgr*",
    "demente", "dementi", "d3mente", "d3ment1", "demen*",
    "handicappato", "handicappati", "hand1capp4t0", "handic*",
    "mongoloide", "mongoloidi", "mong0l01de", "mongol*",
    "manicomio", "man1c0m10", "manic*",
    "minorato", "minorati", "m1n0rat0", "m1n0r4t1", "minor*",
    "spastico", "spastici", "spast1c0", "spast1c1", "spast*",
    "cuckold", "cuck0ld", "cuck", "cornuto", "c0rnut0", "cornu*",

    # Corpo e sessualità
    "culo", "culi", "cul0", "cul1", "culetto", "culetti", "culone",
    "pene", "pen3", "p3ne", "p3n3", "pisello", "pise*",
    "vagina", "vag1na", "v4g1n4", "fessa", "fess4", "fica",
    "tette", "tett3", "t3tt3", "tettone", "tettona", "tett*",
    "pompino", "p0mp1n0", "pomp1no", "p0mpino", "pompi*",
    "succhiare", "succh1are", "succh14re", "succh*",
    "masturbazione", "masturb4z10ne", "masturb*",
    "sperma", "sp3rma", "sp3rm4", "sborra", "sb0rr4", "sbor*",
    "scopare", "sc0p4re", "scopata", "scop4t4", "scopa*",
    "stronzata", "str0nzata", "str0nz4t4", "stron*",
    "inculare", "1ncul4re", "inculat0", "incul*",
    "chiappe", "ch1appe", "ch14ppe", "chiap*",

    # Razzismo e discriminazioni
    "ebreo", "ebr30", "ebre0", "ebrei",
    "giudeo", "giude0", "g1ude0", "giudei",
    "crucco", "crucc0", "crucchi",
    "negro", "negr0", "n3gr0", "negri",
    "frocio", "fr0c10", "froci0", "froci",
    "ricchione", "r1cch10ne", "ricchioni",
    "spastico", "spast1c0", "sp4st1c0", "spastici",
    "zingaro", "z1ngar0", "z1ngar1", "zingari",
    
    # Abbreviazioni e varianti minime
    "str", "stz", "caz", "czz", "mrd", "put", "ptr", "vaf", "vff", "frc", "ngr", "trr", "zng"
]

# Pattern per identificare elusioni di filtro
evasion_patterns = [
    # Spazi inseriti tra le lettere
    r'c\s*a\s*z\s*z\s*o',
    r's\s*t\s*r\s*o\s*n\s*z\s*o',
    r'v\s*a\s*f\s*f\s*a\s*n\s*c\s*u\s*l\s*o',
    r'p\s*u\s*t\s*t\s*a\s*n\s*a',
    r'f\s*r\s*o\s*c\s*i\s*o',
    r'm\s*e\s*r\s*d\s*a',
    r'n\s*e\s*g\s*r\s*o',
    r'c\s*o\s*g\s*l\s*i\s*o\s*n\s*e',
    
    # Separatori e caratteri speciali
    r'c[.,_*+\-]?a[.,_*+\-]?z[.,_*+\-]?z[.,_*+\-]?o',
    r's[.,_*+\-]?t[.,_*+\-]?r[.,_*+\-]?o[.,_*+\-]?n[.,_*+\-]?z[.,_*+\-]?o',
    r'v[.,_*+\-]?a[.,_*+\-]?f[.,_*+\-]?f[.,_*+\-]?a[.,_*+\-]?n[.,_*+\-]?c[.,_*+\-]?u[.,_*+\-]?l[.,_*+\-]?o',
    
    # Leet speak (sostituzione di lettere con numeri o simboli)
    r'c[a4]zz[o0]',
    r'str[o0]nz[o0]',
    r'v[a4]ff[a4]ncul[o0]',
    r'putt[a4]n[a4]',
    r'c[o0]gl[i1][o0]n[e3]',
    r'n[e3]gr[o0]',
    r'm[e3]rd[a4]',
    
    # Vocali ripetute (allungamento)
    r'caaa+z+o+',
    r'strooo+n+z+o+',
    r'vaaaf+a+n+c+u+l+o+',
    r'meeee+r+d+a+',
    
    # Blocco di tentativi di circumvenzione di filtri
    r'[a4]ss[a4]ss[i1]n[o0]',
    r'[o0]m[i1]c[i1]d[i1][o0]',
    r'su[i1]c[i1]d[i1][o0]',
    r'st[u]pr[o0]',
    r'v[i1][o0]l[e3]nz[a4]',
    
    # Violenza e temi sensibili
    r'[a4]mm[a4]zz[a4]r[e3]',
    r'[u]cc[i1]d[e3]r[e3]',
    r'sp[a4]r[a4]r[e3]',
    r'sg[o0]zz[a4]r[e3]',
    r'c[o0]lt[e3]ll[o0]',
    r'f[u]c[i1]l[e3]'
]

# Pattern per identificare phishing o spam
phishing_patterns = [
    # URL sospetti
    r'https?://bit\.ly/\w+',  # URL shortener
    r'https?://tinyurl\.com/\w+',  # URL shortener
    r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+/(?:password|login|verify)',  # URL con parole sospette
    
    # Parole chiave legate al phishing
    r'password|credenziali|accedi|verifica|login',
    r'codice\s+di\s+(?:verifica|sicurezza|accesso)',
    r'pin\s+(?:carta|bancomat|credit|credito)',
    r'dati\s+(?:bancari|carta|credito)',
    r'invia\s+(?:soldi|denaro|euro)',
    
    # Formati di dati sensibili
    r'\b(?:[0-9]{4}[\s\-]?){4}\b',  # possibile numero di carta di credito
    r'\b[A-Za-z0-9._%+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b \w{1,20}',  # email seguita da possibile password
    
    # Contatti sospetti
    r'(?:whatsapp|telegram|signal)\s+[+]?[0-9]{8,15}',  # app di messaggistica con numero
    r'(?:cell|tel|telefono|chiamami)\s+[+]?[0-9]{8,15}', # richiesta di contatto
    
    # Schemi di truffe noti
    r'(?:investi|guadagni?|soldi|denaro).*(?:facil[ei]|veloc[ei]|rapid[oi]|sicur[oi])',
    r'lavoro\s+(?:da\s+casa|online|smart).*(?:\d+\s*[€$]|euro|soldi|guadagn[oi])',
    r'(?:eredità|lotteria|premio).*(?:vinto|ricevuto|contatt[ai])',
    r'bitcoin|ethereum|crypto|criptovalut[ae]'
]

# Lista di domini di phishing noti
known_phishing_domains = [
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "rebrand.ly", "cutt.ly",
    "bl.ink", "tiny.cc", "shorturl.at", "rb.gy", "tny.im", "short.io", "buff.ly", "snip.ly"
]

# Parole chiave per il contesto
context_keywords = {
    "violenza": [
        "uccidere", "ammazzare", "sparare", "accoltellare", "sgozzare", "strangolare", 
        "violento", "violenta", "aggressione", "aggredire", "arma", "armi", "pistola", 
        "coltello", "fucile", "sangue", "morire", "morte", "cadavere", "omicidio", 
        "assassinio", "assassino", "terrorismo", "bomba", "esplosivo", "ucciderò", 
        "ucciderà", "minaccia", "minacciare", "torture", "torturare", "picchiare", 
        "pestare", "massacrare", "mutilare"
    ],
    "suicidio": [
        "suicidio", "suicidarsi", "ammazzarsi", "impiccarsi", "farla finita", 
        "togliersi la vita", "voglio morire", "non voglio più vivere", "morte",
        "overdose", "pillole"
    ],
    "droga": [
        "droga", "droghe", "cocaina", "eroina", "anfetamine", "ecstasy", "lsd", 
        "marijuana", "spacciare", "spaccio", "dose", "pasticche", "hashish",  
        "acidi", "trip", "sniffare", "farsi", "cannabis"
    ],
    "discriminazione": [
        "razzismo", "razzista", "nazismo", "nazista", "fascismo", "fascista", 
        "discriminazione", "discriminare", "inferiore", "superiore", "odiare", 
        "odio", "xenofobia", "xenofobo", "antisemitismo", "antisemita", "omofobia",
        "omofobo", "transfobia", "transfobo", "stranieri", "immigrati"
    ],
    "phishing": [
        "password", "credenziali", "login", "accesso", "banca", "bancario", "bancomat", 
        "carta", "pin", "codice", "verifica", "urgente", "problema", "account", "blocco", 
        "sospensione", "sicurezza", "violazione", "hacker", "clic", "clicca", "contatta", 
        "contattare", "vincita", "premio", "milioni", "lotteria", "eredità", "principe"
    ],
    "spam": [
        "viagra", "cialis", "pillole", "ingrandimento", "pene", "sesso", "dimagrire", 
        "perdere peso", "dimagrisci", "dimagrante", "guadagnare", "guadagni", "guadagno", 
        "facile", "veloce", "ricco", "soldi", "euro", "investimento", "investire", 
        "trading", "forex", "casino", "scommesse", "scommessa", "affare", "occasione"
    ]
}

# Inizializzazione del filtro di profanità
profanity.load_censor_words()
profanity.add_censor_words(blacklist_words_it)

# Configurazione per il rilevamento delle ripetizioni
REPEAT_THRESHOLD = 5  # Caratteri identici ripetuti
CAPS_THRESHOLD = 0.7  # Percentuale di caratteri maiuscoli

# Dizionario dei tentativi di elusione
evasion_attempts = {}

# Funzione per normalizzare il testo prima dell'analisi
def normalize_text(text):
    if not text:
        return ""
    
    # Converti in minuscolo
    text = text.lower()
    
    # Rimuovi caratteri speciali usati per camuffare
    text = re.sub(r'[.\-_*\d@$]', '', text)
    
    # Rimuovi spazi extra
    text = re.sub(r'\s+', ' ', text)
    
    # Rimuovi ripetizioni di caratteri
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    
    return text.strip()

# Funzione per calcolare l'entropia (complessità) del testo
def calculate_entropy(text):
    if not text:
        return 0
    
    # Frequenza dei caratteri
    char_freq = {}
    for char in text:
        if char in char_freq:
            char_freq[char] += 1
        else:
            char_freq[char] = 1
    
    # Calcolo dell'entropia
    entropy = 0
    for freq in char_freq.values():
        probability = freq / len(text)
        entropy -= probability * (math.log(probability, 2) if probability > 0 else 0)
    
    return entropy

# Funzione per rilevare ripetizioni e schemi
def detect_repetition_patterns(text):
    if not text:
        return False, None
    
    # Controllo ripetizioni di caratteri
    for match in re.finditer(r'(.)\1{' + str(REPEAT_THRESHOLD) + ',}', text):
        return True, f"Rilevata ripetizione eccessiva di caratteri: '{match.group()}'"
    
    # Controllo testo in maiuscolo
    uppercase_count = sum(1 for c in text if c.isupper())
    if len(text) > 5 and uppercase_count / len(text) > CAPS_THRESHOLD:
        return True, "Rilevato uso eccessivo di MAIUSCOLE"
    
    # Controllo righe vuote eccessive
    if text.count('\n\n\n') > 2:
        return True, "Rilevato uso eccessivo di righe vuote"
    
    # Controllo ripetizioni di parole
    words = text.lower().split()
    if len(words) > 3:
        # Controlla sequenze ripetute
        for i in range(len(words) - 2):
            if words[i:i+3] == words[i+3:i+6]:
                return True, "Rilevata ripetizione di frasi"
    
    return False, None

# Funzione per rilevare potenziali URL e analizzarli
def extract_and_check_urls(text):
    if not text:
        return []
    
    # Trova URL
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
    suspicious_urls = []
    
    for url in urls:
        try:
            # Parse dell'URL
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Controllo domini di phishing noti
            if any(phishing_domain in domain for phishing_domain in known_phishing_domains):
                suspicious_urls.append((url, "dominio di URL shortener sospetto"))
                continue
            
            # Controllo parametri sospetti nell'URL
            query_params = urllib.parse.parse_qs(parsed_url.query)
            suspicious_params = ['password', 'email', 'login', 'token', 'account', 'verify']
            
            for param in suspicious_params:
                if param in query_params:
                    suspicious_urls.append((url, f"parametro sospetto nell'URL: {param}"))
                    break
            
            # Controllo di stringhe con caratteri che appaiono simili (homograph attack)
            homograph_chars = ['0', 'о', 'O', 'l', 'I', '1']  # zero, cirillico o, O maiuscola, l, I, uno
            domain_parts = domain.split('.')
            
            for part in domain_parts:
                if any(char in part for char in homograph_chars):
                    suspicious_urls.append((url, "possibile attacco homograph (caratteri simili)"))
                    break
        
        except Exception as e:
            logger.error(f"Errore nell'analisi dell'URL {url}: {e}")
    
    return suspicious_urls

# Funzione per controllare con OpenAI
def check_with_openai(text, user_id=None):
    if not text or text.strip() == "":
        return False, None
    
    try:
        logger.info(f"Invio richiesta a OpenAI Moderation API per: '{text[:50]}...'")
        response = openai.Moderation.create(input=text)
        results = response["results"][0]
        
        # Se il contenuto è flaggato come inappropriato
        if results["flagged"]:
            # Ottieni le categorie specifiche
            categories = results["categories"]
            flagged_categories = [cat for cat, flagged in categories.items() if flagged]
            
            # Ottieni i punteggi di categoria
            scores = results["category_scores"]
            highest_score = 0
            highest_category = ""
            
            for category, score in scores.items():
                if score > highest_score and categories[category]:
                    highest_score = score
                    highest_category = category
            
            logger.warning(f"OpenAI ha rilevato contenuto inappropriato: {flagged_categories}")
            return True, f"Contenuto bloccato: OpenAI ha rilevato {highest_category} (confidence: {highest_score:.2f})"
        
        return False, None
    except Exception as e:
        logger.error(f"Errore durante la verifica con OpenAI: {e}")
        # Fallback ai metodi locali in caso di errore
        return False, None

# Funzione per rilevare spam e pattern di phishing
def check_phishing(text, user_id=None):
    if not text or text.strip() == "":
        return False, None
    
    text_lower = text.lower()
    normalized_text = normalize_text(text_lower)
    
    # Tracking del comportamento dell'utente (per future implementazioni)
    user_key = user_id if user_id else "anonymous"
    if user_key not in evasion_attempts:
        evasion_attempts[user_key] = {"count": 0, "last_attempt": 0}
    
    # Controlla pattern di phishing
    for pattern in phishing_patterns:
        if re.search(pattern, text_lower):
            matches = re.findall(pattern, text_lower)
            logger.info(f"Pattern di phishing rilevato: {matches}")
            # Incrementa il contatore di tentativi
            evasion_attempts[user_key]["count"] += 1
            evasion_attempts[user_key]["last_attempt"] = time.time()
            return True, f"Possibile tentativo di phishing rilevato: {matches[0]}"
    
    # Estrai e controlla URL
    suspicious_urls = extract_and_check_urls(text)
    if suspicious_urls:
        logger.info(f"URL sospetti rilevati: {suspicious_urls}")
        evasion_attempts[user_key]["count"] += 1
        evasion_attempts[user_key]["last_attempt"] = time.time()
        return True, f"URL sospetto rilevato: {suspicious_urls[0][0]} - {suspicious_urls[0][1]}"
    
    # Controlla parole chiave di contesto legate al phishing
    phishing_keywords = context_keywords.get("phishing", []) + context_keywords.get("spam", [])
    matches = [word for word in phishing_keywords if word in text_lower.split() or f" {word} " in f" {text_lower} "]
    
    if len(matches) >= 2:  # Se ci sono almeno 2 parole chiave di phishing
        logger.info(f"Parole chiave di phishing rilevate: {matches}")
        return True, f"Possibile tentativo di phishing: multipli indicatori ({', '.join(matches[:3])})"
    
    return False, None

# Funzione per controllare contenuti violenti
def check_violent_content(text):
    if not text or text.strip() == "":
        return False, None
    
    text_lower = text.lower()
    normalized_text = normalize_text(text_lower)
    
    # Parole chiave relative alla violenza
    violence_keywords = context_keywords.get("violenza", []) + context_keywords.get("suicidio", [])
    matches = [word for word in violence_keywords if word in text_lower.split() or f" {word} " in f" {text_lower} "]
    
    # Se ci sono almeno 2 parole chiave relative alla violenza
    if len(matches) >= 2:
        logger.info(f"Contenuto violento rilevato: {matches}")
        return True, f"Contenuto bloccato: potenziale contenuto violento o pericoloso ({', '.join(matches[:3])})"
    
    return False, None

# Funzione per controllare le parole offensive usando le librerie e la blacklist
def check_profanity(text):
    if not text or text.strip() == "":
        return False, None
    
    original_text = text
    text_lower = text.lower()
    normalized_text = normalize_text(text_lower)
    
    # Debug per vedere cosa sta succedendo
    logger.debug(f"Checking profanity for: '{text}' (normalized: '{normalized_text}')")
    
    # 0. Controllo diretto sulla stringa originale (per maggiore sicurezza)
    for word in blacklist_words_it:
        if word in text_lower:
            logger.info(f"Profanità rilevata (controllo diretto): '{word}' in '{text_lower}'")
            return True, f"Contenuto bloccato: uso di linguaggio inappropriato ('{word}')"
    
    # 1. Controllo con la blacklist personalizzata su testo normalizzato
    for word in blacklist_words_it:
        if word in normalized_text.split() or f" {word} " in f" {normalized_text} ":
            logger.info(f"Profanità rilevata: parola in blacklist '{word}' in '{normalized_text}'")
            return True, f"Contenuto bloccato: uso di linguaggio inappropriato ('{word}')"
    
    # 2. Controllo pattern di evasione
    for pattern in evasion_patterns:
        if re.search(pattern, normalized_text):
            match = re.search(pattern, normalized_text)
            matched_text = match.group(0) if match else pattern
            logger.info(f"Profanità rilevata: pattern di evasione '{matched_text}' in '{normalized_text}'")
            return True, f"Contenuto bloccato: tentativo di eludere il filtro di moderazione"
    
    # 3. Controllo per parole di contesto problematiche
    context_matches = {}
    for category, keywords in context_keywords.items():
        matches = []
        for keyword in keywords:
            if keyword in normalized_text.split() or f" {keyword} " in f" {normalized_text} ":
                matches.append(keyword)
        
        if matches:
            context_matches[category] = matches
    
    # Se ci sono almeno 2 corrispondenze in una categoria specifica
    for category, matches in context_matches.items():
        if len(matches) >= 2:
            logger.info(f"Contenuto sospetto rilevato: categoria {category}, parole {matches}")
            return True, f"Contenuto bloccato: linguaggio potenzialmente inappropriato ({category}: {', '.join(matches[:3])})"
    
    # 4. Controllo con better_profanity
    if profanity.contains_profanity(original_text):
        logger.info(f"Profanità rilevata: rilevamento della libreria better_profanity nel testo '{original_text}'")
        return True, "Contenuto bloccato: uso di linguaggio inappropriato"
    
    # 5. Controllo ripetizioni e pattern
    has_repetition, repetition_reason = detect_repetition_patterns(original_text)
    if has_repetition:
        logger.info(f"Pattern di ripetizione rilevato: {repetition_reason}")
        return True, f"Contenuto bloccato: {repetition_reason}"
    
    logger.info(f"Nessuna profanità rilevata nel testo: '{original_text}'")
    return False, None

# Funzione principale per filtrare i messaggi in arrivo
def filter_message(message, user_id=None, context=None):
    if not message or message.strip() == "":
        return "", None
    
    # Log di debug
    logger.debug(f"Filtraggio messaggio: '{message[:100]}...' da utente: {user_id}" if len(message) > 100 else f"Filtraggio messaggio: '{message}' da utente: {user_id}")
    print(f"[DEBUG] Filtraggio messaggio: '{message[:50]}...'" if len(message) > 50 else f"[DEBUG] Filtraggio messaggio: '{message}'")
    
    # VERIFICA BASE SEMPLICE E DIRETTA (massima priorità)
    # Controlla direttamente per contenuti offensivi senza normalizzazione
    for word in blacklist_words_it:
        if word in message.lower():
            logger.warning(f"RAPIDO: Contenuto offensivo bloccato, contiene: {word}")
            print(f"[DEBUG] Parola bloccata trovata: '{word}'")
            return "Questo messaggio è stato censurato per contenuti inappropriati.", {
                "original": message,
                "censored": profanity.censor(message),
                "reason": f"Linguaggio inappropriato ('{word}')",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "category": "profanity_direct"
            }
    
    # Prova a usare OpenAI se possibile
    try:
        is_inappropriate, openai_reason = check_with_openai(message, user_id)
        if is_inappropriate:
            logger.warning(f"Messaggio bloccato da OpenAI: {openai_reason}")
            print(f"[DEBUG] OpenAI ha bloccato: {openai_reason}")
            return "Questo messaggio è stato bloccato dal sistema di moderazione AI.", {
                "original": message,
                "reason": openai_reason,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "category": "openai_moderation"
            }
    except Exception as e:
        logger.error(f"Errore nel controllo OpenAI: {e}")
        # Continua con i controlli locali
    
    # 1. Verifica phishing (priorità alta)
    is_phishing, phishing_reason = check_phishing(message, user_id)
    if is_phishing:
        logger.warning(f"Tentativo di phishing bloccato: {phishing_reason}")
        print(f"[DEBUG] Phishing bloccato: {phishing_reason}")
        return "Questo messaggio è stato bloccato perché potrebbe contenere un tentativo di phishing.", {
            "original": message,
            "reason": phishing_reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "category": "phishing"
        }
    
    # 2. Verifica contenuti violenti (priorità alta)
    is_violent, violent_reason = check_violent_content(message)
    if is_violent:
        logger.warning(f"Contenuto violento bloccato: {violent_reason}")
        print(f"[DEBUG] Contenuto violento bloccato: {violent_reason}")
        return "Questo messaggio è stato bloccato perché potrebbe contenere riferimenti a violenza.", {
            "original": message,
            "reason": violent_reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "category": "violent_content"
        }
    
    # 3. Verifica profanità con better_profanity direttamente
    if profanity.contains_profanity(message):
        logger.warning(f"Profanità diretta rilevata in: {message}")
        print(f"[DEBUG] Profanità rilevata (better_profanity)")
        return "Questo messaggio è stato censurato per contenuti inappropriati.", {
            "original": message,
            "censored": profanity.censor(message),
            "reason": "Uso di linguaggio inappropriato (better_profanity)",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "category": "profanity_direct_lib"
        }
    
    # 4. Verifica il contenuto con i filtri locali per profanità
    is_profane, profanity_reason = check_profanity(message)
    if is_profane:
        logger.warning(f"Messaggio bloccato per profanità: {profanity_reason}")
        print(f"[DEBUG] Profanità rilevata: {profanity_reason}")
        
        # Versione censurata del messaggio
        censored_message = profanity.censor(message)
        
        return "Questo messaggio è stato censurato per contenuti inappropriati.", {
            "original": message,
            "censored": censored_message,
            "reason": profanity_reason,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "category": "profanity"
        }
    
    # Se tutti i controlli passano, restituisci il messaggio originale
    logger.info("Messaggio approvato")
    print("[DEBUG] Messaggio approvato")
    return message, None

# Funzione per moderare contenuti più lunghi come post o articoli
def moderate_long_content(content, title=None, author_id=None):
    if not content or content.strip() == "":
        return "", None
    
    # Combina titolo e contenuto se entrambi sono presenti
    full_content = f"{title}: {content}" if title else content
    
    # Log di debug
    logger.debug(f"Moderazione contenuto lungo: '{full_content[:100]}...' da autore: {author_id}" if len(full_content) > 100 else f"Moderazione contenuto lungo: '{full_content}' da autore: {author_id}")
    
    # VERIFICA DIRETTA PER CONTENUTI OFFENSIVI
    for word in blacklist_words_it:
        if word in full_content.lower():
            logger.warning(f"RAPIDO: Contenuto lungo con contenuto offensivo bloccato, contiene: {word}")
            return "Questo contenuto è stato censurato per linguaggio inappropriato.", {
                "reason": f"Linguaggio inappropriato ('{word}')",
                "author_id": author_id,
                "timestamp": datetime.now().isoformat(),
                "category": "profanity_direct"
            }
    
    # Prova a usare OpenAI se possibile
    try:
        is_inappropriate, openai_reason = check_with_openai(full_content, author_id)
        if is_inappropriate:
            logger.warning(f"Contenuto lungo bloccato da OpenAI: {openai_reason}")
            return "Questo contenuto è stato bloccato dal sistema di moderazione AI.", {
                "original": full_content,
                "reason": openai_reason,
                "author_id": author_id,
                "timestamp": datetime.now().isoformat(),
                "category": "openai_moderation"
            }
    except Exception as e:
        logger.error(f"Errore nel controllo OpenAI per contenuto lungo: {e}")
        # Continua con i controlli locali
    
    # Usa la stessa funzione di moderazione usata per i messaggi
    result, info = filter_message(full_content, author_id)
    if result != full_content:
        return result, info
    
    logger.info("Contenuto lungo approvato")
    return content, None

# Tentativo di importare le librerie opzionali
try:
    import math
except ImportError:
    # Definizione semplificata di log se math non è disponibile
    def math():
        class _Math:
            def log(self, x, base):
                return 0 if x <= 0 else 1
        return _Math()
    math = math()