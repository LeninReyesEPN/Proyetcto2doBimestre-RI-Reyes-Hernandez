from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from backend.corpus import download_and_prepare_corpus
from backend.vector_db import build_index
from backend.rag import generate_rag_response, record_user_feedback
from backend.evaluation import run_evaluation

# Initialize FastAPI
app = FastAPI(title="Multimodal RAG API", description="Servicio RAG con CLIP, FAISS y Gemini para e-commerce")

# Enable CORS for Next.js development server requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[MessageItem]] = []

class FeedbackRequest(BaseModel):
    query: str
    product_id: str
    feedback: str # 'like' or 'dislike'

@app.on_event("startup")
def startup_event():
    print("Iniciando servicio y preparando datos...")
    try:
        # Pre-load corpus and vector index on startup if they don't exist
        download_and_prepare_corpus()
        build_index()
    except Exception as e:
        print(f"Error durante la inicialización de inicio: {e}")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert pydantic history list to raw dict list for compatibility
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        response = generate_rag_response(request.query, history_dicts)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    if request.feedback not in ["like", "dislike"]:
        raise HTTPException(status_code=400, detail="El feedback debe ser 'like' o 'dislike'")
    try:
        record_user_feedback(request.query, request.product_id, request.feedback)
        return {"status": "success", "message": "Feedback de relevancia guardado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/evaluate")
async def evaluate_endpoint():
    try:
        baseline_metrics = run_evaluation(apply_reranking=False)
        reranked_metrics = run_evaluation(apply_reranking=True)
        return {
            "status": "success",
            "metrics": {
                "baseline_faiss": baseline_metrics,
                "with_reranking": reranked_metrics
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/index")
async def index_endpoint():
    try:
        build_index()
        return {"status": "success", "message": "Base vectorial FAISS reindexada con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
