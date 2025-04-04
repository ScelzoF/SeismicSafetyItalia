
from datetime import datetime, timedelta

def get_italy_dst_offset(now=None):
    if not now:
        now = datetime.utcnow()
    year = now.year
    march_last = datetime(year, 3, 31)
    while march_last.weekday() != 6:
        march_last -= timedelta(days=1)
    october_last = datetime(year, 10, 31)
    while october_last.weekday() != 6:
        october_last -= timedelta(days=1)
    return 2 if march_last < now < october_last else 1

def get_orario():
    utc_now = datetime.utcnow()
    offset = get_italy_dst_offset(utc_now)
    italy_now = utc_now + timedelta(hours=offset)
    return {
        "utc": utc_now.strftime('%H:%M:%S'),
        "italia": italy_now.strftime('%H:%M:%S'),
        "diff": f"+{offset}h"
    }
