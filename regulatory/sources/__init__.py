from .base import sync_source

REGISTRY = [
    {"id": "rbi_notifications", "regulator": "RBI", "url": "https://rbi.org.in/notifications_rss.xml",
     "method": "rss", "coverage": "Current RSS window; not a complete historical archive", "interval_seconds": 3600},
    {"id": "sebi_master_circulars", "regulator": "SEBI",
     "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=6",
     "method": "listing", "coverage": "First listing page plus previously discovered URLs", "interval_seconds": 3600},
    {"id": "sebi_circulars", "regulator": "SEBI",
     "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7",
     "method": "listing", "coverage": "First listing page plus previously discovered URLs", "interval_seconds": 3600},
]


def sync_all(store, limit=5):
    return [sync_source(store, source, limit) for source in REGISTRY]
