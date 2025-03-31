import logging
import re
import time
import hashlib
import urllib.parse
from datetime import datetime

# Configurazione del sistema di logging
logging.basicConfig(
    level=logging.DEBUG,  # Aumentato a DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("moderazione_contenuti")

# Blacklist di parole offensive in italiano (versione ridotta per debug)
blacklist_words_it = [
    "stronzo", "stronza", "stronzi", "stronze",
    "cazzo", "cazzi", 
    "merda", "merde",
    "puttana", "vaffanculo", "coglione"
]

# Funzione semplificata per filtrare i messaggi
def filter_message(message, user_id=None, context=None):
    if not message or message.strip() == "":
        return "", None
    
    # Log di debug
    logger.debug(f"Filtraggio messaggio: '{message}' da utente: {user_id}")
    
    # Test diretto con stampa per debug
    message_lower = message.lower()
    print(f"[DEBUG] Filtraggio messaggio: '{message_lower}'")
    
    # Controllo blacklist rapido
    for word in blacklist_words_it:
        if word in message_lower:
            print(f"[DEBUG] Parola bloccata trovata: '{word}'")
            logger.warning(f"Contenuto bloccato, contiene: {word}")
            return "Questo messaggio è stato censurato per contenuti inappropriati.", {
                "original": message,
                "reason": f"Linguaggio inappropriato ('{word}')",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "category": "profanity_direct"
            }
    
    # Se passa il controllo
    logger.info("Messaggio approvato")
    return message, None

# Funzione per moderare contenuti più lunghi
def moderate_long_content(content, title=None, author_id=None):
    # Versione semplificata per debug
    return filter_message(content, author_id)