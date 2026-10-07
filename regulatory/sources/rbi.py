import xml.etree.ElementTree as ET
from .base import validate_url


def discover(raw, base_url):
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise ValueError("Expected an RSS feed; DTDs are not accepted")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("RBI RSS is unavailable or changed format") from exc
    refs = []
    for item in root.findall(".//item"):
        url, title = item.findtext("link", "").strip(), item.findtext("title", "").strip()
        try:
            validate_url(url, "RBI", resolve=False)
        except ValueError:
            continue
        if title:
            refs.append({"url": url, "title": title, "published_at": item.findtext("pubDate")})
    return refs
