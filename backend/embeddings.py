import numpy as np
from sentence_transformers import SentenceTransformer

# Load a lightweight, publicly available CLIP model
# It maps text and images to the same common vector space.
# We will use 'clip-ViT-B-32' or 'sentence-transformers/clip-ViT-B-32'
MODEL_NAME = 'clip-ViT-B-32'
_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Cargando el modelo multimodal CLIP ({MODEL_NAME})...")
        try:
            # We initialize SentenceTransformer with the CLIP model
            _model = SentenceTransformer(MODEL_NAME)
            print("CLIP cargado exitosamente.")
        except Exception as e:
            print(f"Error al cargar CLIP de sentence-transformers: {e}")
            print("Cargando modelo SentenceTransformer por defecto como fallback...")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def encode_text(texts: list[str]) -> np.ndarray:
    """Generates embeddings for text queries or descriptions."""
    model = get_model()
    # Normalize embeddings to easily compute cosine similarity via dot product
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)
