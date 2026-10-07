from urllib.parse import urljoin
from .base import Page, validate_url, decode_html


def discover(raw, base_url):
    refs = {}
    for link, title in Page(decode_html(raw)).links:
        url = urljoin(base_url, link)
        if not any(path in url for path in ("/legal/circulars/", "/legal/master-circulars/")) or not url.endswith(".html"):
            continue
        try:
            validate_url(url, "SEBI", resolve=False)
        except ValueError:
            continue
        if title.strip():
            refs[url] = {"url": url, "title": " ".join(title.split())}
    return list(refs.values())
