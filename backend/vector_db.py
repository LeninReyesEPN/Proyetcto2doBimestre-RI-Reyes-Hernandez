import os
import json
import numpy as np
import faiss
from backend.embeddings import encode_text, encode_image

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
    image_urls = [item.get("image_url") for item in corpus]

    # 1. Embeddings de texto (título del producto) con la torre de texto de CLIP
    text_embeddings = encode_text(texts)

    # 2. Embeddings de imagen (descarga + torre visual de CLIP). Recuperación multimodal:
    #    cuando la imagen del producto está disponible, el vector indexado combina texto
    #    e imagen; si la descarga falla (URL caída, timeout), se usa solo el de texto.
    print(f"Generando embeddings visuales con CLIP para {len(image_urls)} imágenes de producto...")
    image_embeddings = encode_image(image_urls)

    fused_embeddings = []
    n_with_image = 0
    for text_vec, image_vec in zip(text_embeddings, image_embeddings):
        if image_vec is not None:
            combined = text_vec + image_vec
            norm = np.linalg.norm(combined)
            fused_embeddings.append(combined / norm if norm > 0 else text_vec)
            n_with_image += 1
        else:
            fused_embeddings.append(text_vec)

    print(f"Embeddings multimodales (texto+imagen) generados para {n_with_image}/{len(corpus)} productos "
          f"({len(corpus) - n_with_image} indexados solo con texto por imagen no disponible).")

    embeddings = np.array(fused_embeddings, dtype=np.float32)
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
