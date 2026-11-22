"""Read explicit current alert statements, not arbitrary color words in a page."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import re
import unicodedata

from bs4 import BeautifulSoup
import requests

UNKNOWN = "NON DISPONIBILE"
OFFICIAL_URLS = {
    "campi_flegrei": "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/campi-flegrei/",
    "vesuvio": "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/vesuvio/",
    "ischia": "https://rischi.protezionecivile.gov.it/it/vulcanico/vulcani-italia/ischia/",
}
_AREA_NAMES = {
    "campi_flegrei": r"(?:i\s+)?campi\s+flegrei",
    "vesuvio": r"(?:il\s+)?vesuvio",
    "ischia": "ischia",
}


def parse_current_alert(html, area):
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text.lower())
        if not unicodedata.combining(c)
    )
    text = " ".join(text.split())
    pattern = (
        r"\battualmente\s+il\s+livello\s+di\s+allerta\s+(?:per|al)\s+"
        + _AREA_NAMES[area]
        + r"\s+e\s+(verde|giallo|arancione|rosso)\b"
    )
    matches = set(re.findall(pattern, text))
    # Missing, changed or contradictory wording must not become a green badge.
    return matches.pop().upper() if len(matches) == 1 else UNKNOWN


def fetch_official_alert_levels():
    def fetch(item):
        area, url = item
        try:
            response = requests.get(
                url, timeout=(3, 6), verify=True,
                headers={"User-Agent": "SeismicSafetyItalia/2.0"},
            )
            response.raise_for_status()
            # Parse bytes so the HTML charset is respected. requests.text can
            # default to Latin-1 for text/html responses without a charset.
            return area, parse_current_alert(response.content, area)
        except (requests.RequestException, ValueError):
            return area, UNKNOWN

    with ThreadPoolExecutor(max_workers=3) as workers:
        result = dict(workers.map(fetch, OFFICIAL_URLS.items()))
    result["source"] = "Protezione Civile — pagine ufficiali; N/D se non verificabile"
    result["_source"] = result["source"]
    result["sources"] = OFFICIAL_URLS.copy()
    result["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    return result
