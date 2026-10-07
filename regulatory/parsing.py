"""Conservative paragraph/section locators; no claim of legal-semantic parsing."""
import hashlib
import re
from difflib import SequenceMatcher


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def clauses(text):
    result = []
    section = "preamble"
    page = None
    pending = []

    def flush():
        content = " ".join(pending)
        pending.clear()
        while content:
            end = len(content) if len(content) <= 1800 else content.rfind(" ", 0, 1800)
            if end <= 0:
                end = 1800
            part, content = content[:end], content[end:].lstrip()
            result.append({"locator": f"paragraph-{len(result)+1}", "section": section,
                           "page": page, "text": part, "text_hash": digest(part)})

    for line in text.splitlines():
        line = " ".join(line.split())
        if not line:
            flush()
            continue
        if re.fullmatch(r"\[PAGE \d+\]", line):
            flush()
            page = int(re.search(r"\d+", line).group())
            continue
        match = re.match(r"^(\d{1,3}(?:\.\d+)*[.)]?|[IVX]+\.)\s+", line)
        if match:
            flush()
            section = match.group(1).rstrip(".)")
        pending.append(line)
    flush()
    return result


def diff_clauses(old, new):
    matcher = SequenceMatcher(None, [x["text"] for x in old], [x["text"] for x in new], autojunk=False)
    changes = []
    for tag, a, b, c, d in matcher.get_opcodes():
        if tag == "equal":
            continue
        changes.append({"type": {"replace": "modified", "delete": "removed", "insert": "added"}[tag],
                        "before": old[a:b], "after": new[c:d], "review_status": "pending",
                        "materiality": "not_assessed"})
    return changes


def candidate_conditions(text):
    lower = text.lower()
    types = []
    for target, pattern in [("ppi_issuer", r"\bppi\b|prepaid payment instrument"),
                            ("payment_aggregator", r"payment aggregator"),
                            ("stock_broker", r"stock.?broker")]:
        if re.search(pattern, lower):
            types.append(target)
    return {"entity_types": types, "jurisdiction": "IN", "activity": None}


def obligation_candidates(items):
    return [{"clause_id": item["id"], "action": item["text"], "quote": item["text"],
             "conditions": candidate_conditions(item["text"]), "review_status": "pending"}
            for item in items if re.search(r"\b(shall|must|required to)\b", item["text"], re.I)]
