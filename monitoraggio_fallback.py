
import time
import logging

import requests

try:
    import monitoraggio_ingv as ingv
except ImportError:
    ingv = None

try:
    import monitoraggio_usgs as usgs
except ImportError:
    usgs = None

FONTE_ATTIVA = {"fonte": "INGV", "ultimo_check": time.time()}

def dati_sismici():
    global FONTE_ATTIVA
    try:
        start = time.time()
        # Timeout implicito: massimo 5 secondi per ottenere i dati
        data = ingv.dati_sismici()
        elapsed = time.time() - start
        if elapsed > 5:
            raise TimeoutError("Timeout INGV superato")
        if FONTE_ATTIVA["fonte"] != "INGV":
            logging.info("Fonte INGV ripristinata.")
        FONTE_ATTIVA = {"fonte": "INGV", "ultimo_check": time.time()}
        return data, "Fonte: INGV"
    except Exception as e:
        logging.warning(f"[Fallback] Errore INGV: {e}")
        try:
            data = usgs.dati_sismici()
            if FONTE_ATTIVA["fonte"] != "USGS":
                logging.info("Fonte INGV non disponibile. Passaggio temporaneo a USGS.")
            FONTE_ATTIVA = {"fonte": "USGS", "ultimo_check": time.time()}
            return data, "Fonte temporanea: USGS (INGV non disponibile)"
        except Exception as e2:
            logging.error(f"[Fallback] Errore USGS: {e2}")
            return None, "Errore: impossibile ottenere dati da INGV e USGS."
