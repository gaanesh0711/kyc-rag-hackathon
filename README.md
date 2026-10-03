# FinVisors

Public regulatory research demo for compliance, legal, risk, and audit teams.
The interface uses the Evidence desk direction: forest green, warm ivory,
readable typography, and retrieved source records beside the answer.

## What works

A user asks a regulatory question. FastAPI embeds the query using
all-MiniLM-L6-v2, retrieves three similar company records from the existing
Chroma store, and asks Gemini to answer from those excerpts. The API returns
the question, answer, company/regulator/sector metadata, and full retrieved
excerpts. The frontend renders Markdown without accepting raw HTML.

The dataset is a bundled FinVisory research document. This demo does not
verify identities, screen sanctions, calculate risk scores, accept customer
uploads, or provide real-time regulatory updates.

## Local setup

Backend (Python 3.11 or newer recommended):

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env

Set GEMINI_API_KEY (or GOOGLE_API_KEY) in the root .env, then:

    python main.py

Frontend (Node 22.12 or newer):

    cd frontend
    npm ci
    copy .env.example .env
    npm run dev

The development frontend defaults to http://127.0.0.1:8000. Open the Vite
URL shown in the terminal. The workspace is at /#workspace.

## Netlify frontend

netlify.toml sets base frontend, build npm run build, publish dist, and
Node 22. Set VITE_API_BASE_URL to the separately hosted backend's public
HTTPS origin (no trailing /ask). Rebuild after changing it. Without this
variable, the production interface displays Backend not connected and
requests return an actionable error. No model key belongs in VITE_ variables:
those variables are included in public client bundles.

Hash navigation does not require special route handling; the included
SPA rewrite also allows the app entry to be served on direct URLs.

## Separate Python backend

Use a Python service/container with persistent storage for chroma_db and
access to download the sentence-transformer model. Do not deploy this
long-running FastAPI/Chroma/Python process as static files on Netlify.

Start from the repository root:

    uvicorn main:app --host 0.0.0.0 --port 8000

Set GEMINI_API_KEY on the backend only. Set CORS_ORIGINS to the exact Netlify
site origin (and explicitly allow any preview origins being used), separated
by commas. Enable HTTPS at the host. The health endpoint reports ready or
degraded according to chain initialization. Browser health failures do not
prevent retrying a question. /ask retains its existing response contract.

The API permits 10 requests per client IP per minute and at most three
concurrent queries per process. These are demo guards, not a distributed
abuse/cost-control system. Before a public production rollout, set provider
quotas and host-level rate limits. Configure trusted proxy handling at the
host; behind an unconfigured proxy, visitors may share one IP allowance.
Browser cancellation stops waiting; already-running provider work may
continue. The client times out after 90 seconds.

If serving the UI from FastAPI instead, build the frontend with
VITE_API_BASE_URL set to that API's public origin before starting the backend.
FastAPI serves frontend/dist, not frontend source files.

## Dataset maintenance

The existing index and source PDF have been preserved. python ingest.py
rebuilds the index using the existing dataset-specific parser. Back up the
store before rebuilding: the original script removes the previous directory.
Retrieval is similarity-based and does not guarantee single-company matches.
Source records are context, not independently verified claim-level citations.

## Checks

    cd frontend
    npm run lint
    npm run build

Python API contract tests use a fake chain to avoid provider charges and
model downloads:

    pip install -r requirements-dev.txt
    python -m unittest discover -s tests -v

Browser checks exercise API-shaped fixtures separately from the product;
there are no hard-coded answers in the application. Live Gemini behavior
requires a valid backend key and an initialized vector store.

## Later phases

Private uploads, persistent research history, team accounts, OCR, and
identity/sanctions integrations require backend work and separate product
decisions. None are represented as active capabilities in this demo.
