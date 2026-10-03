# Verification

- Frontend production build: passed (Vite 8.3.2).
- Frontend lint: passed (Oxlint pinned to the repository's declared 1.79.0;
  the resolved newer native Windows runtime failed to load).
- API contract suite: 8 tests passed using a fake RAG chain. Checks cover
  question bounds, complete excerpts and metadata, provider/init errors,
  readiness status, allowed/disallowed CORS, rate limits, and capacity limits.
- Browser interaction checks: passed with API-shaped test fixtures. Verified
  question submission, source display, expandable excerpts, no-source state,
  malformed responses, safe Markdown, errors/retry, message rotation, cancellation,
  mobile navigation, skip link, and no horizontal overflow at 320/390/768/1440px.
- Production bundle: renders correctly. Missing VITE_API_BASE_URL gives an explicit
  Backend not connected state and actionable request error.
- Desktop and mobile screenshots inspected.
- Git whitespace check: passed.

Test fixtures exist only in verification scripts, not application code.
No live Gemini query was performed: no provider key is available in this checkout.
No Netlify deployment or live backend configuration was changed.
Existing ingest.py, rag_chain.py, source PDF, and committed vector index are unchanged.

Before live deployment: provide the backend HTTPS origin, configure its server-side
Gemini key and persistent storage, allow the frontend origin through CORS_ORIGINS,
and configure VITE_API_BASE_URL in Netlify before building. Set backend/provider
quotas before exposing the demo publicly.
