# ui_templates/app_fastapi.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.llm_engine import LLMEngine
from core.rag_pipeline import SimpleHybridRAG, RAGResponse

app = FastAPI(title="Enterprise AI Assessment API", version="1.0.0")

llm = LLMEngine()
rag = SimpleHybridRAG(llm)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 4

@app.get("/health")
def health_check():
    return {"status": "ok", "provider": llm.provider, "model": llm.model}

@app.post("/api/rag_query", response_model=RAGResponse)
def rag_query_endpoint(req: QueryRequest):
    try:
        return rag.query(req.query, top_k=req.top_k, structured=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {
        "message": "Enterprise AI Assessment API is running!",
        "docs_url": "http://127.0.0.1:8000/docs"
    }