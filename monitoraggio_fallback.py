
import time
import logging

try:
    import monitoraggio_ingv as ingv
except ImportError:
    ingv = None

try:
    import monitoraggio_usgs as usgs
except ImportError:
    usgs = None

# Stato della fonte attiva
FONTE_ATTIVA = {"fonte": "INGV", "ultimo_check": time.time()}

def dati_sismici():
    global FONTE_ATTIVA

    try:
        # Prova a ottenere dati da INGV
        data = ingv.dati_sismici()
        if FONTE_ATTIVA["fonte"] != "INGV":
            logging.info("Fonte INGV ripristinata.")
        FONTE_ATTIVA = {"fonte": "INGV", "ultimo_check": time.time()}
        return data, "Fonte: INGV"
    except Exception as e:
        logging.warning(f"Errore INGV: {e}")
        try:
            data = usgs.dati_sismici()
            if FONTE_ATTIVA["fonte"] != "USGS":
                logging.info("Fonte INGV non disponibile. Passaggio temporaneo a USGS.")
            FONTE_ATTIVA = {"fonte": "USGS", "ultimo_check": time.time()}
            return data, "Fonte temporanea: USGS (INGV non disponibile)"
        except Exception as e2:
            logging.error(f"Errore USGS: {e2}")
            return None, "Errore: impossibile ottenere dati da INGV e USGS."
