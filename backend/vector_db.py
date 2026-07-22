import os
import json
import numpy as np
import faiss
from backend.embeddings import encode_text

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CORPUS_PATH = os.path.join(DATA_DIR, "corpus.json")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")

# In-memory corpus cache and FAISS index
_corpus = []
_index = None
_product_id_map = [] # Maps index offset to product ID

def load_corpus():
    global _corpus
    if not _corpus:
        if not os.path.exists(CORPUS_PATH):
            raise FileNotFoundError(f"El corpus no existe en {CORPUS_PATH}. Ejecuta corpus.py primero.")
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            _corpus = json.load(f)
    return _corpus

def build_index():
    global _index, _product_id_map
    corpus = load_corpus()
    if not corpus:
        print("El corpus está vacío. Imposible indexar.")
        return

    print("Indexando el corpus en la base de datos vectorial FAISS...")
    # Prepare text to encode (product titles)
    texts = [item["title"] for item in corpus]
    
    # Generate embeddings
    embeddings = encode_text(texts) # float32 numpy array
    dimension = embeddings.shape[1]
    
    # IndexFlatIP uses Inner Product (which is Cosine Similarity since vectors are normalized)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    
    # Save the index
    faiss.write_index(index, INDEX_PATH)
    
    # Save product mapping
    product_ids = [item["product_id"] for item in corpus]
    with open(INDEX_PATH + ".map", "w", encoding="utf-8") as f:
        json.dump(product_ids, f)
        
    _index = index
    _product_id_map = product_ids
    print(f"Indexación completada. {len(product_ids)} productos guardados en {INDEX_PATH}")

def load_index():
    global _index, _product_id_map
    if _index is None:
        if not os.path.exists(INDEX_PATH) or not os.path.exists(INDEX_PATH + ".map"):
            build_index()
        else:
            _index = faiss.read_index(INDEX_PATH)
            with open(INDEX_PATH + ".map", "r", encoding="utf-8") as f:
                _product_id_map = json.load(f)
    return _index, _product_id_map

def search(query_text: str, top_k: int = 5) -> list[dict]:
    """Retrieves top-k closest products from the FAISS vector index."""
    index, id_map = load_index()
    corpus = load_corpus()
    
    # 1. Encode query
    query_vector = encode_text([query_text]) # shape (1, dim)
    
    # 2. Search FAISS
    scores, indices = index.search(query_vector, top_k)
    
    # 3. Format results
    results = []
    # Index elements
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        p_id = id_map[idx]
        # Retrieve product metadata from corpus
        product = next((item for item in corpus if item["product_id"] == p_id), None)
        if product:
            results.append({
                "product_id": p_id,
                "title": product["title"],
                "image_url": product["image_url"],
                # Cosine similarity score as float, rounded to 4 decimals
                "similarity": float(score)
            })
    return results

if __name__ == "__main__":
    # Test indexing
    build_index()
    # Test search
    res = search("nike running shoes", top_k=2)
    print("Test Search Results:", res)
