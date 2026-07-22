import io
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image
from sentence_transformers import SentenceTransformer

# Load a lightweight, publicly available CLIP model
# It maps text and images to the same common vector space.
# We will use 'clip-ViT-B-32' or 'sentence-transformers/clip-ViT-B-32'
MODEL_NAME = 'clip-ViT-B-32'
_model = None

IMAGE_TIMEOUT_SECONDS = 6
IMAGE_DOWNLOAD_WORKERS = 16

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

def _download_image(url: str):
    """Downloads a single product image and decodes it as RGB. Returns None on any failure
    (dead link, timeout, corrupt file) so a broken URL never stops the whole indexing run."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=IMAGE_TIMEOUT_SECONDS)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception:
        return None

def encode_image(image_urls: list[str]) -> list:
    """Downloads product images concurrently and generates a CLIP embedding per URL using the
    same model's vision tower. Returns a list aligned with image_urls; entries are None where
    the image could not be downloaded, so callers can fall back to text-only embeddings."""
    model = get_model()

    with ThreadPoolExecutor(max_workers=IMAGE_DOWNLOAD_WORKERS) as executor:
        images = list(executor.map(_download_image, image_urls))

    valid_indices = [i for i, img in enumerate(images) if img is not None]
    if not valid_indices:
        return [None] * len(image_urls)

    valid_images = [images[i] for i in valid_indices]
    valid_embeddings = model.encode(valid_images, normalize_embeddings=True, show_progress_bar=False)

    results = [None] * len(image_urls)
    for idx, embedding in zip(valid_indices, valid_embeddings):
        results[idx] = np.array(embedding, dtype=np.float32)
    return results
