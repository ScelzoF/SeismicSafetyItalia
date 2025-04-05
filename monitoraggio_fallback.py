
import time
import logging
import os

try:
    import monitoraggio_ingv as ingv
except ImportError:
    ingv = None

try:
    import monitoraggio_usgs as usgs
except ImportError:
    usgs = None

FONTE_ATTIVA = {"fonte": "INGV", "ultimo_check": time.time()}

# Timeout configurabile
TIMEOUT_SECONDS = 5

# Abilita diagnostica visibile lato utente (può essere passato da Streamlit)
last_error_message = ""

def dati_sismici(show_debug=False):
    global FONTE_ATTIVA, last_error_message

    try:
        start = time.time()
        data = ingv.dati_sismici()
        elapsed = time.time() - start

        if elapsed > TIMEOUT_SECONDS:
            raise TimeoutError("Timeout INGV superato")

        if FONTE_ATTIVA["fonte"] != "INGV":
            logging.info("Fonte INGV ripristinata.")

        FONTE_ATTIVA = {"fonte": "INGV", "ultimo_check": time.time()}
        last_error_message = ""
        return data, "Fonte: INGV"

    except Exception as e:
        last_error_message = f"[Fallback] Errore INGV: {e}"
        logging.warning(last_error_message)

        try:
            data = usgs.dati_sismici()
            if FONTE_ATTIVA["fonte"] != "USGS":
                logging.info("Fonte INGV non disponibile. Passaggio temporaneo a USGS.")

            FONTE_ATTIVA = {"fonte": "USGS", "ultimo_check": time.time()}
            last_error_message = ""
            return data, "Fonte temporanea: USGS (INGV non disponibile)"

        except Exception as e2:
            last_error_message = f"[Fallback] Errore USGS: {e2}"
            logging.error(last_error_message)
            if show_debug:
                return None, f"⚠️ Connessione remota non disponibile (INGV e USGS non raggiungibili)\n{last_error_message}"
            else:
                return None, "⚠️ Connessione remota non disponibile (INGV e USGS non raggiungibili)"
