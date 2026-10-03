"""FinVisors public research API. Run from any working directory."""
import logging
import os
import time
from collections import OrderedDict
from pathlib import Path
from threading import Lock, BoundedSemaphore
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from rag_chain import get_rag_chain, RetrievalQAChain

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
logger = logging.getLogger(__name__)
app = FastAPI(title="FinVisors Regulatory Research API", version="1.1.0")
origins = [origin.strip() for origin in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=False, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"])
chain: Optional[RetrievalQAChain] = None
chain_lock = Lock()
request_slots = BoundedSemaphore(3)
rate_lock = Lock()
# A bounded, per-process demo guard. Use an edge limiter for multiple workers.
request_counts = OrderedDict()


def initialize_chain():
    global chain
    with chain_lock:
        if chain is None:
            chain = get_rag_chain(persist_directory=str(ROOT / "chroma_db"))
    return chain


@app.on_event("startup")
def startup_event():
    try:
        initialize_chain()
    except Exception:
        logger.exception("RAG startup failed; initialization will be retried on request")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceDetail(BaseModel):
    company: Optional[str] = None
    regulator: Optional[str] = None
    vertical: Optional[str] = None
    document: Optional[str] = None
    excerpt: Optional[str] = None


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceDetail]


DIST = ROOT / "frontend" / "dist"
if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/")
def serve_ui():
    if (DIST / "index.html").exists():
        return FileResponse(DIST / "index.html")
    return health_check()


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    icon = DIST / "favicon.svg"
    if icon.exists():
        return FileResponse(icon, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Frontend has not been built.")


@app.get("/health")
def health_check():
    return {"status": "ready" if chain is not None else "degraded",
            "service": "FinVisors Regulatory Research API",
            "chain_initialized": chain is not None}


def check_demo_limit(client: str):
    now = time.monotonic()
    with rate_lock:
        started, count = request_counts.get(client, (now, 0))
        if now - started >= 60:
            started, count = now, 0
        if count >= 10:
            raise HTTPException(status_code=429,
                detail="The public demo allows 10 questions per minute. Please wait and try again.",
                headers={"Retry-After": str(max(1, int(60 - (now - started))))})
        request_counts[client] = (started, count + 1)
        request_counts.move_to_end(client)
        while len(request_counts) > 10000:
            request_counts.popitem(last=False)


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, http_request: Request):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    check_demo_limit(http_request.client.host if http_request.client else "unknown")
    if not request_slots.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="The research service is busy. Please try again shortly.")
    try:
        try:
            active_chain = initialize_chain()
        except Exception:
            logger.exception("RAG initialization failed")
            raise HTTPException(status_code=503,
                detail="The research service is not ready. Please try again shortly.") from None
        try:
            result = active_chain.invoke({"query": question})
        except Exception:
            logger.exception("Research query failed")
            raise HTTPException(status_code=502,
                detail="The research provider could not complete the request. Please try again.") from None
        sources = []
        for doc in result.get("source_documents", []):
            meta = doc.metadata or {}
            sources.append(SourceDetail(company=meta.get("company_name"),
                regulator=meta.get("regulator"), vertical=meta.get("vertical"),
                document=meta.get("source_doc"), excerpt=doc.page_content))
        return AskResponse(question=question, answer=result.get("result", ""), sources=sources)
    finally:
        request_slots.release()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST", "127.0.0.1"),
                port=int(os.getenv("PORT", "8000")), reload=False)
