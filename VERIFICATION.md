# Verification

- Frontend production build: passed (Vite 8.3.2).
- Frontend lint: passed (Oxlint pinned to the repository's declared 1.79.0;
  the resolved newer native Windows runtime failed to load).
- API contract suite: 8 tests passed using a fake RAG chain. Checks cover
  question bounds, complete excerpts and metadata, provider/init errors,
  readiness status, allowed/disallowed CORS, rate limits, and capacity limits.
- Simulator suite: 8 additional tests passed for full selected scope, exact
  filters, empty scope, input bounds, evidence mapping, duplicate/invented IDs,
  incomplete provider responses, and sanitized provider errors.
- Browser interaction checks: passed with API-shaped test fixtures. Verified
  question submission, source display, expandable excerpts, no-source state,
  malformed responses, safe Markdown, errors/retry, message rotation, cancellation,
  mobile navigation, skip link, and no horizontal overflow at 320/390/768/1440px.
- Production bundle: renders correctly. Missing VITE_API_BASE_URL gives an explicit
  Backend not connected state and actionable request error.
- Desktop and mobile screenshots inspected.
- Git whitespace check: passed.

Test fixtures exist only in verification scripts, not application code.
Local live verification on 2026-10-03:
- Replaced locally installed PyTorch 2.14.1 with the official 2.13.0 CPU wheel
  after Smart App Control blocked its native DLL. Security settings stayed enabled.
- Backend /health reports ready with the existing retrieval chain initialized.
- Live /ask returned a Gemini answer and three retrieved source records.
- Production preview at http://127.0.0.1:5174 passed browser health, CORS,
  question submission, answer rendering, and source display against the real backend.
- The key is configured privately in the ignored backend environment file.
- Live simulator wallet preset completed in the browser: all 10 selected records
  assessed with expandable evidence. A whole-dataset API review completed all
  80 records (76 distinct company labels), returning 13 potential impacts and
  67 no-clear-link assessments for that test scenario. These are illustrative
  model inferences, not validated applicability decisions.
- Simulator mobile layout checked at 390px with no horizontal overflow.

No Netlify deployment was performed. Existing ingest.py, rag_chain.py, and source
PDF are unchanged. Chroma updated local database/index files during live use;
these runtime changes have not been committed.

Before live deployment: provide the backend HTTPS origin, configure its server-side
Gemini key and persistent storage, allow the frontend origin through CORS_ORIGINS,
and configure VITE_API_BASE_URL in Netlify before building. Set backend/provider
quotas before exposing the demo publicly.
