import os
import json
import time
import google.generativeai as genai
from sentence_transformers import CrossEncoder
from backend.vector_db import search as vector_search

# Lista de modelos en orden de preferencia.
# gemini-3.1-flash-lite es el más liviano: menor consumo de cuota por petición
GEMINI_MODELS = [
    "gemini-3.1-flash-lite",      # Más económico - modelo prioritario
    "gemini-2.0-flash-lite",      # Alternativa liviana
    "gemini-2.0-flash",           # Flash estándar
    "gemini-1.5-flash",           # Flash de generación anterior
    "gemini-1.5-flash-8b",        # El más pequeño disponible
]

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FEEDBACK_PATH = os.path.join(DATA_DIR, "feedback.json")

# In-memory Cross-Encoder cache
_cross_encoder = None

def get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        print("Cargando modelo Cross-Encoder para Re-ranking...")
        try:
            _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("Cross-Encoder cargado exitosamente.")
        except Exception as e:
            print(f"Error al cargar Cross-Encoder: {e}. Se desactivará el re-ranking de excelencia.")
            _cross_encoder = None
    return _cross_encoder

def get_gemini_client(model_name: str = None):
    # Retrieve API key from env variable
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ADVERTENCIA: GEMINI_API_KEY no configurada. Las llamadas al LLM fallarán.")
    genai.configure(api_key=api_key)
    model = model_name or GEMINI_MODELS[0]
    return genai.GenerativeModel(model)

def call_gemini_with_fallback(prompt: str) -> str:
    """Intenta llamar a Gemini con múltiples modelos y reintentos ante error 429."""
    for model_name in GEMINI_MODELS:
        for attempt in range(3):  # Hasta 3 reintentos por modelo
            try:
                client = get_gemini_client(model_name)
                response = client.generate_content(prompt)
                print(f"Respuesta exitosa con modelo: {model_name}")
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                    print(f"Cuota excedida en {model_name} (intento {attempt+1}/3). Esperando {wait_time}s...")
                    time.sleep(wait_time)
                elif "404" in error_str or "no longer available" in error_str.lower():
                    print(f"Modelo {model_name} no disponible. Probando siguiente modelo...")
                    break  # Pasar al siguiente modelo
                else:
                    print(f"Error inesperado con {model_name}: {e}")
                    break  # Pasar al siguiente modelo
    raise Exception("Todos los modelos de Gemini fallaron o agotaron su cuota.")

def load_feedback_db() -> dict:
    if os.path.exists(FEEDBACK_PATH):
        try:
            with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_feedback_db(db: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def record_user_feedback(query: str, product_id: str, feedback_type: str):
    """Saves user feedback for subsequent relevance feedback retrieval adjustments."""
    db = load_feedback_db()
    key = f"{query.lower().strip()}||{product_id}"
    # like = +1, dislike = -1
    score_delta = 1 if feedback_type == "like" else -1
    db[key] = score_delta
    save_feedback_db(db)
    print(f"Feedback registrado para '{query}' -> '{product_id}': {feedback_type}")

def apply_relevance_feedback(query: str, candidates: list[dict]) -> list[dict]:
    """Adjusts similarity scores of candidates based on stored user relevance feedback."""
    db = load_feedback_db()
    adjusted = []
    for item in candidates:
        p_id = item["product_id"]
        key = f"{query.lower().strip()}||{p_id}"
        delta = db.get(key, 0)
        
        # Apply a minor score adjustment (e.g. +10% or -10% score)
        adjusted_score = item["similarity"] + (delta * 0.1)
        # Keep score bound within [0.0, 1.0]
        adjusted_score = max(0.0, min(1.0, adjusted_score))
        
        item_copy = item.copy()
        item_copy["similarity"] = adjusted_score
        adjusted.append(item_copy)
    return adjusted

def expand_query_with_llm(query: str, chat_history: list) -> str:
    """Query Expansion (Bonus): Rewrites the query to improve vector retrieval."""
    try:
        system_prompt = (
            "Eres un asistente de búsqueda. Tu tarea es expandir la consulta de búsqueda del usuario para "
            "incluir términos relacionados, sinónimos y palabras clave asociadas a e-commerce que ayuden a "
            "recuperar los productos correctos. Retorna ÚNICAMENTE la consulta expandida en una sola línea, "
            "sin explicaciones adicionales.\n"
            f"Consulta original: {query}"
        )
        expanded = call_gemini_with_fallback(system_prompt)
        print(f"Consulta original: '{query}' -> Consulta expandida: '{expanded}'")
        return expanded
    except Exception as e:
        print(f"Error al expandir consulta con LLM: {e}. Se utilizará la consulta original.")
        return query

def generate_rag_response(query: str, chat_history: list[dict] = []) -> dict:
    """RAG pipeline integrating query expansion, vector search, cross-encoder re-ranking, and Gemini LLM."""
    print(f"Procesando consulta RAG: '{query}'...")
    
    # 1. Query Expansion (Excelencia)
    expanded_query = expand_query_with_llm(query, chat_history)
    
    # 2. Vector Search (CLIP + FAISS)
    initial_results = vector_search(expanded_query, top_k=8)
    
    # 3. Apply Relevance Feedback (Excelencia)
    feedback_results = apply_relevance_feedback(query, initial_results)
    
    # 4. Re-ranking (Excelencia)
    final_evidences = []
    cross_encoder = get_cross_encoder()
    if cross_encoder and feedback_results:
        # Cross-encoder evaluates (query, product_title) pairs
        pairs = [(query, res["title"]) for res in feedback_results]
        ce_scores = cross_encoder.predict(pairs)
        
        # Attach cross-encoder scores and sort candidates
        for i, score in enumerate(ce_scores):
            feedback_results[i]["re_rank_score"] = float(score)
            
        # Sort by re-rank score descending
        re_ranked = sorted(feedback_results, key=lambda x: x["re_rank_score"], reverse=True)
        # Select top-4 re-ranked evidences
        final_evidences = re_ranked[:4]
        print("Re-ranking aplicado con Cross-Encoder.")
    else:
        # Fallback to top-4 raw CLIP/feedback results
        final_evidences = feedback_results[:4]
        print("Búsqueda vectorial estándar utilizada (sin Re-ranking).")

    # 5. Build RAG Prompt Context
    context_str = ""
    for i, item in enumerate(final_evidences):
        context_str += f"Producto {i+1} [ID: {item['product_id']}]:\n"
        context_str += f"Título: {item['title']}\n"
        context_str += f"Similitud de recuperación: {item['similarity']:.2f}\n\n"
        
    # 6. Format Chat History (Memoria Conversacional - Excelencia)
    history_str = ""
    # Only take last 6 messages to fit context limits
    for msg in chat_history[-6:]:
        role_label = "Usuario" if msg["role"] == "user" else "Asistente"
        history_str += f"{role_label}: {msg['content']}\n"
        
    system_prompt = (
        "Eres un asistente de compras inteligente. Tu tarea es responder la consulta del usuario de "
        "manera profesional y útil, basándote ÚNICAMENTE en el contexto de productos recuperados provisto a continuación. "
        "Si los productos recuperados no se relacionan con la consulta, explícalo de forma amable.\n\n"
        f"### Historial de conversación:\n{history_str}\n"
        f"### Contexto de productos recuperados:\n{context_str}\n"
        f"### Consulta del usuario: {query}\n"
        "Genera tu respuesta final:"
    )
    
    # 7. Query LLM Gemini (con fallback automático entre modelos)
    answer = "Lo siento, no he podido contactar al servicio de inteligencia artificial de Gemini en este momento."
    try:
        answer = call_gemini_with_fallback(system_prompt)
    except Exception as e:
        print(f"Error al llamar al LLM Gemini (todos los modelos fallaron): {e}")
        # Fallback: respuesta basada directamente en los productos recuperados
        answer = (
            f"⚠️ El servicio de Gemini no está disponible en este momento (cuota excedida o sin API key).\n\n"
            f"**Productos recuperados para tu búsqueda '{query}':**\n" +
            "\n".join([f"- **{item['title']}** (Similitud: {item['similarity']*100:.1f}%)" for item in final_evidences])
        )

    return {
        "answer": answer,
        "evidences": final_evidences
    }
