"""Bounded official-source fetcher. No credentials, URL input API, or browser bypass."""
import io
import ipaddress
import socket
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import httpx
from pypdf import PdfReader

HOSTS = {"RBI": {"rbi.org.in", "www.rbi.org.in", "rbidocs.rbi.org.in"},
         "SEBI": {"sebi.gov.in", "www.sebi.gov.in"}}
MAX_BYTES = 20 * 1024 * 1024


def decode_html(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def validate_url(url, regulator, resolve=True):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in HOSTS[regulator] or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Only HTTPS URLs on the regulator's approved hosts are allowed")
    if resolve:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("Source did not resolve to public addresses")


def fetch(url, regulator):
    with httpx.Client(timeout=30, follow_redirects=False, trust_env=False, headers={"User-Agent": "FinVisors-Research/2.0 (bounded regulatory monitoring)"}) as client:
        for _ in range(5):
            validate_url(url, regulator)
            with client.stream("GET", url) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = urljoin(url, response.headers["location"])
                    continue
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_BYTES:
                        raise ValueError("Source exceeds the 20 MB ingestion limit")
                return bytes(data), response.headers.get("content-type", ""), url
    raise ValueError("Too many source redirects")


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.links, self.embeds, self.lines = [], [], []
        self.anchor, self.skipping = None, 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.skipping += 1
        if tag in ("p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4"):
            self.lines.append("\n")
        if tag == "a":
            self.anchor = [attrs.get("href", ""), ""]
        if tag in ("iframe", "embed", "object"):
            self.embeds.append(attrs.get("src", attrs.get("data", "")))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skipping = max(0, self.skipping - 1)
        if tag == "a" and self.anchor:
            self.links.append(tuple(self.anchor))
            self.anchor = None

    def handle_data(self, value):
        if not self.skipping:
            self.lines.append(value)
            if self.anchor:
                self.anchor[1] += value

    @property
    def text(self):
        return "\n".join(line.strip() for line in "".join(self.lines).splitlines() if line.strip())


def normalize(raw, content_type):
    if raw.startswith(b"%PDF"):
        reader = PdfReader(io.BytesIO(raw))
        if len(reader.pages) > 600:
            raise ValueError("PDF exceeds 600-page parser limit")
        return "\n".join(f"[PAGE {i+1}]\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages))
    if "html" not in content_type:
        raise ValueError("Expected an HTML or text-based PDF regulatory document")
    text = Page(decode_html(raw)).text
    if len(text) < 4000 and any(term in text.lower() for term in ["captcha", "access denied", "request rejected", "enable javascript", "checking your browser"]):
        raise ValueError("Source returned an access challenge; manual access is required")
    return text


def fetch_document(ref, regulator):
    raw, kind, url = fetch(ref["url"], regulator)
    if not raw.startswith(b"%PDF") and "html" in kind:
        page = Page(decode_html(raw))
        candidates = page.embeds + [link for link, _ in page.links if ".pdf" in link.lower()]
        for candidate in candidates:
            # SEBI's PDF viewer sometimes embeds the official PDF in a file query argument.
            from urllib.parse import parse_qs
            candidate = parse_qs(urlsplit(candidate).query).get("file", [candidate])[0]
            candidate = urljoin(url, candidate)
            try:
                validate_url(candidate, regulator, resolve=False)
            except ValueError:
                continue
            if ".pdf" in candidate.lower():
                raw, kind, url = fetch(candidate, regulator)
                break
    text = normalize(raw, kind)
    if len(text) > 4_000_000:
        raise ValueError("Extracted text exceeds ingestion limit")
    return raw, text, {"status": "draft" if any(w in ref["title"].lower() for w in ("draft", "consultation")) else "unreviewed",
                       "publication_date": ref.get("published_at"), "effective_from": None,
                       "retrieved_url": url, "extraction": "text_pdf_or_html", "clause_locator": "heuristic_paragraph"}


def sync_source(store, source, limit=5):
    from .rbi import discover as rbi_discover
    from .sebi import discover as sebi_discover
    result = {"status": "ok", "discovered": 0, "checked": 0, "new_versions": 0, "errors": [], "coverage": source["coverage"]}
    try:
        raw, _, _ = fetch(source["url"], source["regulator"])
        refs = (rbi_discover if source["method"] == "rss" else sebi_discover)(raw, source["url"])
        result["discovered"] = len(refs)
        if not refs:
            raise ValueError("No document links found; listing parser or source needs review")
        # Revisit known documents as well as new discovery; a stable URL may change in place.
        known = [{"url": v["url"], "title": v["title"]} for v in store.versions() if v["source_id"] == source["id"]]
        candidates = {ref["url"]: ref for ref in refs[:limit] + known[:limit]}
        for ref in candidates.values():
            try:
                data, text, metadata = fetch_document(ref, source["regulator"])
                event = store.ingest(source_id=source["id"], regulator=source["regulator"], raw=data, text=text,
                                     metadata=metadata, url=ref["url"], title=ref["title"])
                result["new_versions"] += int(event["created"])
                result["checked"] += 1
            except (ValueError, httpx.HTTPError, OSError) as exc:
                result["errors"].append({"url": ref["url"], "error": type(exc).__name__})
            time.sleep(0.5)
        if result["errors"]:
            result["status"] = "partial" if result["checked"] else "failed"
    except (ValueError, httpx.HTTPError, OSError) as exc:
        result["status"] = "failed"
        result["errors"].append({"error": type(exc).__name__})
    store.record_sync(source["id"], result)
    return {"source_id": source["id"], **result}
