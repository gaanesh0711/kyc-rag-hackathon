# FinVisors implementation plan

Approved direction: Evidence desk, exact brand FinVisors, public research demo.

1. Consolidate frontend/index.html and src/App.jsx into the Vite React entry.
2. Build a responsive landing page with honest dataset coverage and product boundaries.
3. Build a research workspace using the existing POST /ask contract: question,
   answer, and retrieved source records. Preserve backend/provider/embedding architecture.
4. Add loading scan, 28 rotating research messages, cancellation, request timeout,
   retry, copy feedback, initial/no-source states, and live service availability.
5. Improve the public API's CORS, request bounds, error handling, demo request limits,
   and built-frontend serving. Return complete retrieved excerpts for inspection.
6. Add environment examples, Netlify static configuration, dependency lockfile,
   and separate-backend setup instructions. Keep provider secrets server-side.
7. Verify lint/build, desktop/mobile browser behavior, safe Markdown rendering,
   error/cancel flows, and API response contracts without charging a provider.
8. Present the reviewable changes on a dedicated branch. A live deployment requires
   the actual backend host URL and its Gemini key; those remain server configuration.

Out of scope: document upload, identity verification, sanctions screening, risk
scores, login, persistent history, and fabricated metrics or customer claims.
