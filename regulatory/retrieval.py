"""Lexical + optional MiniLM retrieval, fused by rank; never confidence scoring."""
import math
import re
from collections import Counter
from datetime import date
from functools import lru_cache
from threading import Lock

from .engine import temporal, version_conflicts

lock = Lock()


def tokens(text):
    return re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*", text.lower())


@lru_cache(maxsize=1)
def embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache(maxsize=2)
def vectors(texts):
    return embedder().encode(list(texts), normalize_embeddings=True)


def search(store, question, regulator=None, as_of=None, effective_only=True, semantic=False, limit=6):
    as_of = as_of or date.today().isoformat()
    versions = [v for v in store.versions() if v["source_kind"] == "official"]
    conflicts = version_conflicts(versions, as_of)
    selected, excluded = [], 0
    latest = {}
    for version in versions:
        latest[version["document_id"]] = max(latest.get(version["document_id"], 0), version["number"])
    for version in versions:
        if regulator and version["regulator"] != regulator:
            continue
        if effective_only:
            if temporal(version, as_of)[0] != "effective" or version["document_id"] in conflicts:
                excluded += 1
                continue
        elif version["number"] != latest[version["document_id"]]:
            continue
        for item in store.version(version["id"])["clauses"]:
            selected.append({**item, "version": version})
    counts = [Counter(tokens(item["text"])) for item in selected]
    query = set(tokens(question))
    avg = sum(sum(c.values()) for c in counts) / max(1, len(counts))
    frequencies = {word: sum(word in c for c in counts) for word in query}
    scores = []
    for c in counts:
        score = sum(math.log(1 + (len(counts) - frequencies[word] + .5) / (frequencies[word] + .5)) *
                    (c[word] * 2.5 / (c[word] + 1.5 * (.25 + .75 * sum(c.values()) / max(1, avg))))
                    for word in query if c[word])
        scores.append(score)
    lexical = sorted([i for i, score in enumerate(scores) if score > 0], key=lambda i: scores[i], reverse=True)[:30]
    ranks = {i: 1 / (61 + rank) for rank, i in enumerate(lexical)}
    mode = "lexical_bm25"
    fallback = None
    if semantic and selected:
        try:
            with lock:
                matrix = vectors(tuple(item["text"] for item in selected))
                query_vector = embedder().encode(question, normalize_embeddings=True)
                similarity = matrix @ query_vector
            # This threshold only filters retrieval noise; it is not legal confidence.
            semantic_rank = sorted([i for i, score in enumerate(similarity) if score > .25], key=lambda i: similarity[i], reverse=True)[:30]
            for rank, index in enumerate(semantic_rank):
                ranks[index] = ranks.get(index, 0) + 1 / (61 + rank)
            mode = "bm25_minilm_rank_fusion"
        except Exception:
            fallback = "Semantic retrieval unavailable; lexical search used."
    evidence = [selected[i] for i in sorted(ranks, key=ranks.get, reverse=True)[:limit]]
    return {"question": question, "as_of": as_of, "evidence": evidence,
            "retrieval_mode": mode, "retrieval_notice": fallback, "excluded_versions": excluded,
            "conflicting_documents": len(conflicts), "eligible_clauses": len(selected),
            "answer": "Review the matching official passages below. This response is extractive; it does not infer legal applicability." if evidence else
                      "Insufficient eligible official evidence. Import sources and review status/effective dates, or explicitly include unreviewed material for research.",
            "evidence_status": "reviewed_source_passages" if evidence and effective_only else "unreviewed_source_passages" if evidence else "insufficient",
            "method": "extractive_regulation_search_v2.0", "model": "all-MiniLM-L6-v2" if mode.startswith("bm25_minilm") else None}
