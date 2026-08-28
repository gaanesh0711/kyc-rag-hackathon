import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from rag_chain import get_rag_chain, query_rag, RetrievalQAChain

load_dotenv()

app = FastAPI(
    title="KYC & Fintech Regulatory RAG API",
    description="RAG API for fintech regulatory compliance, KYC requirements, and entity impact queries.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chain instance
chain: Optional[RetrievalQAChain] = None


@app.on_event("startup")
def startup_event():
    global chain
    print("Initializing RAG Chain on startup...")
    try:
        chain = get_rag_chain()
        print("RAG Chain successfully initialized.")
    except Exception as e:
        print(f"Warning: RAG Chain initialization deferred or failed: {e}")


class AskRequest(BaseModel):
    question: str = Field(..., example="What SEBI-related regulatory challenges does Zerodha face?")


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


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve Frontend static directory if present
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def serve_ui():
    frontend_index = os.path.join("frontend", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {
        "status": "healthy",
        "service": "KYC Regulatory RAG API",
        "chain_initialized": chain is not None
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "KYC Regulatory RAG API",
        "chain_initialized": chain is not None
    }



@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    global chain
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        if chain is None:
            chain = get_rag_chain()

        result = chain.invoke({"query": request.question})

        answer = result.get("result", "")
        raw_sources = result.get("source_documents", [])

        sources = []
        for doc in raw_sources:
            meta = doc.metadata or {}
            sources.append(
                SourceDetail(
                    company=meta.get("company_name"),
                    regulator=meta.get("regulator"),
                    vertical=meta.get("vertical"),
                    document=meta.get("source_doc"),
                    excerpt=doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                )
            )

        return AskResponse(
            question=request.question,
            answer=answer,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
