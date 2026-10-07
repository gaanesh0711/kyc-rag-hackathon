from collections import Counter
from datetime import date
from fastapi import APIRouter, HTTPException, Query, Request
from .engine import evaluate, version_conflicts
from .models import Ask, Comparison, Scenario
from .retrieval import search
from .sources import REGISTRY


def router(store, rate_limit, semantic=False):
    api = APIRouter(prefix="/v2")

    def entities(ids):
        available = store.entities()
        if not ids:
            return available
        if not set(ids).issubset({e["id"] for e in available}):
            raise HTTPException(400, "Unknown entity profile")
        return [e for e in available if e["id"] in ids]

    def record(kind, request, result):
        audit_id = store.audit(kind, {"input": request, "output": result, "engine_version": "2.0", "prompt_version": None})
        return {**result, "audit_id": audit_id}

    @api.get("/status")
    def status():
        return {"version": "kyc-rag_V2", "sources": REGISTRY, "sync_runs": store.sync_status(),
                "documents": len({v["document_id"] for v in store.versions()}), "versions": len(store.versions()),
                "profiles": len(store.entities()), "monitoring": "Requires the separate CLI watch process",
                "reviewed_profiles": sum(bool(e["review"]) for e in store.entities())}

    @api.get("/entities")
    def entity_list():
        return store.entities()

    @api.get("/regulations")
    def regulations():
        return store.versions()

    @api.get("/regulations/{document_id}/versions")
    def versions(document_id: str):
        return store.versions(document_id)

    @api.get("/versions/{version_id}")
    def version(version_id: str):
        try:
            return store.version(version_id)
        except KeyError:
            raise HTTPException(404, "Version not found") from None

    @api.get("/changes")
    def changes():
        return store.changes()

    @api.get("/obligations")
    def obligations():
        return store.obligations()

    @api.post("/ask")
    def ask(payload: Ask, request: Request):
        rate_limit(request)
        result = search(store, payload.question.strip(), payload.regulator,
                        payload.as_of.isoformat() if payload.as_of else None, payload.effective_only, semantic)
        return record("regulation_search", payload.model_dump(mode="json"), result)

    @api.post("/impact/{obligation_id}")
    def impact(obligation_id: str, request: Request, as_of: date | None = None):
        rate_limit(request)
        obligation = next((o for o in store.obligations() if o["id"] == obligation_id), None)
        if not obligation:
            raise HTTPException(404, "Obligation not found")
        at = (as_of or date.today()).isoformat()
        conditions = obligation["review"]["conditions"] if obligation["review"] else obligation["conditions"]
        results = [evaluate(e, conditions, obligation=obligation, as_of=at, conflicts=version_conflicts(store.versions(), at)) for e in entities([])]
        return record("actual_impact", {"obligation_id": obligation_id, "as_of": at},
                      {"obligation": obligation, "results": results, "counts": dict(Counter(item["outcome"] for item in results))})

    @api.post("/simulate")
    def simulate(payload: Scenario, request: Request):
        rate_limit(request)
        results = [evaluate(entity, payload.conditions.model_dump(), hypothetical=True) for entity in entities(payload.entity_ids)]
        return record("hypothetical_scenario", payload.model_dump(), {"hypothetical": True, "rule": payload.rule,
            "conditions": payload.conditions.model_dump(), "results": results, "counts": dict(Counter(item["outcome"] for item in results)),
            "assumptions": "The selected conditions are user-stated assumptions; rule text is not automatically interpreted as an applicability rule."})

    @api.post("/compare")
    def compare(payload: Comparison, request: Request, limit: int = Query(default=20, ge=1, le=50)):
        rate_limit(request)
        selected = entities(payload.entity_ids)
        if len(selected) < 2:
            raise HTTPException(400, "Select at least two different entities")
        at = (payload.as_of or date.today()).isoformat()
        obligations = store.obligations()
        # Prioritize reviewed material; the same bounded obligation set is used for every company.
        obligations.sort(key=lambda item: bool(item["review"] and item["review"]["status"] == "approved"), reverse=True)
        conflicts = version_conflicts(store.versions(), at)
        rows = [{"obligation": o, "results": [evaluate(e, o["review"]["conditions"] if o["review"] else o["conditions"],
                    obligation=o, as_of=at, conflicts=conflicts) for e in selected]} for o in obligations[:limit]]
        return record("comparison", payload.model_dump(mode="json"), {"as_of": at, "entities": selected,
            "rows": rows, "total_obligations": len(obligations), "reviewed_rows": len(rows)})

    # Audit content is retrieved via an unguessable per-result capability, not a public list.
    @api.get("/audit/{audit_id}")
    def audit(audit_id: str):
        import json
        with store.connect() as db:
            row = db.execute("SELECT * FROM audit WHERE id=?", (audit_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Audit record not found")
        return {"id": row["id"], "created_at": row["created_at"], "kind": row["kind"], "data": json.loads(row["data"])}

    return api
