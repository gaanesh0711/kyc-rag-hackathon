# Running and reviewing KYC RAG V2

V2 branch: `kyc-rag_V2`. The base branches are preserved; do not merge V2 over the base just to run it.

## Local run

Use the root README Python and frontend dependency setup. Keep the provider key only in the backend `.env`. V2's source monitoring, deterministic applicability and lexical official search do not require a model key. The existing company RAG does.

PowerShell, from the V2 repository root:

```powershell
$env:PORT = '8001'
$env:CORS_ORIGINS = 'http://127.0.0.1:5175,http://localhost:5175'
$env:V2_SEMANTIC_SEARCH = 'true'
python main.py
```

In `frontend/.env`, set the public, non-secret `VITE_API_BASE_URL=http://127.0.0.1:8001`. Then in another terminal:

```powershell
cd frontend
npm ci
npm run build
npm run preview -- --host 127.0.0.1 --port 5175 --strictPort
```

Open http://127.0.0.1:5175/#v2/regulations. The original local demo can continue on port 5174 with its own backend at 8000.

`REGULATORY_DB` optionally changes the database path; default is `data_v2/regulatory.sqlite3`. Back it up along with the existing company store. Runtime data is intentionally ignored by Git. Do not put private client data in this public research demo.

## Source monitoring

```powershell
python -m regulatory.cli sync --limit 3
python -m regulatory.cli sync --limit 3 --watch
```

Watch polls hourly only while the process runs. It is not an installed operating-system service and is not automatically started by the API. A failed or partial check stays visible in Sources & review. Limit bounds newly discovered and previously known document rechecks per source. This is not complete historical coverage. The fetcher restricts hosts, redirects, bytes, PDF pages and timeouts, and does not bypass challenges or turn failed HTML into regulation text.

Import a specific verified official document:

```powershell
python -m regulatory.cli fetch --regulator SEBI --url 'https://www.sebi.gov.in/legal/master-circulars/jun-2025/master-circular-for-stock-brokers_94623.html' --title 'Master Circular for Stock Brokers'
```

The backend imports 76 distinct company names from the existing 80-record index, read-only, with unreviewed profile attributes. It does not infer a licence from a sector.

## Review workflow

Review commands are local administration, not public HTTP writes. Populate a JSON file using actual reviewed evidence and your real reviewer identifier; do not approve these examples without checking the official source. Dates here illustrate the format only.

Version review fields:

```json
{"reviewer":"Reviewer name","rationale":"Explain verified status and dates, including their source passages","status":"final","publication_date":"2026-01-01","effective_from":"2026-02-01","effective_to":null}
```

Run `python -m regulatory.cli review version VERSION_ID version-review.json`.

Statuses: draft, consultation, final, superseded, withdrawn. Publication is distinct from effectiveness. An end date is exclusive. Superseded/withdrawn versions require a reviewed end date for historical use. Overlapping effective versions of the same document are flagged and excluded until reconciled. Changing bytes or fetching a newer copy does not itself revoke an earlier legal version.

Obligation review fields:

```json
{"reviewer":"Reviewer name","rationale":"Explain the clause's target class and assumptions","status":"approved","conditions":{"entity_types":["ppi_issuer"],"jurisdiction":"IN","activity":null},"action":"Reviewed requirement in plain language","quote":"An exact fragment copied from the linked clause"}
```

Run `python -m regulatory.cli review obligation OBLIGATION_ID obligation-review.json`. Quotes must match the linked clause exactly. A reviewer must reject an unsupported target condition; substring validation alone does not prove legal correctness.

Entity review fields:

```json
{"reviewer":"Reviewer name","rationale":"Explain the profile evidence and validity period","entity_types":["ppi_issuer"],"activities":["customer_onboarding"],"jurisdiction":"IN","effective_from":"2026-01-01","effective_to":null,"source_url":"https://official-evidence.example/profile","complete_entity_types":false}
```

Run `python -m regulatory.cli review entity ENTITY_ID entity-review.json`. Replace the illustrative source URL with real evidence. `complete_entity_types=false` means absence of a target type is UNKNOWN, not exclusion. Set it true only when the scope of the entity-type list is fully reviewed. Review history is preserved. IDs are exposed through `/v2/entities`, `/v2/regulations`, `/v2/obligations`, and the evidence panels.

## Audit and operational limits

Every V2 search, scenario, comparison and actual-impact request produces an append-only audit snapshot. The UI downloads that specific record as JSON; the CLI supports `python -m regulatory.cli export-audit AUDIT_ID new-file.json`. There is no public audit listing. A random audit URL is a capability, not user authentication: anyone with the URL can read the record. Private/team deployment needs authenticated, tenant-scoped authorization and retention controls before storing confidential data.

SQLite triggers prevent normal updates/deletes, but an administrator can alter the database. Do not market these records as tamper-proof. Store the original official bytes and parsed passages as provenance; paragraph/section detection is heuristic. Text diffs are not legal amendment determinations. No OCR, automatic cross-document supersession, full exception logic, licence verification or general contradiction detection is claimed.

The V2 official search returns exact source passages; it does not generate new legal conclusions. Enable MiniLM rank fusion with `V2_SEMANTIC_SEARCH=true`. If semantic retrieval fails, the response explicitly discloses lexical fallback. The existing Gemini company research remains under `/ask`; V2 uses `/v2/ask`.

## Verification

```powershell
python -m unittest discover -s tests_v2 -v
python -m unittest discover -s tests -v
cd frontend
npm run lint
npm run build
```

All reviewed fixtures in automated tests are synthetic and isolated in temporary databases. They are not seeded into the live regulatory library.
