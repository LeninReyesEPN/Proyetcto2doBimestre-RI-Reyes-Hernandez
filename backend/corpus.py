import os
import json
import pandas as pd
from datasets import load_dataset

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CORPUS_PATH = os.path.join(DATA_DIR, "corpus.json")
QRELS_PATH = os.path.join(DATA_DIR, "qrels.json")
SUBSET_SIZE = 1000

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)

def download_and_prepare_corpus():
    print("Iniciando la preparación del corpus multimodal...")
    ensure_dirs()
    
    # Check if cache files already exist
    if os.path.exists(CORPUS_PATH) and os.path.exists(QRELS_PATH):
        print(f"El corpus ya existe en {CORPUS_PATH}. Saltando descarga.")
        return

    try:
        print("Cargando el dataset 'crossingminds/shopping-queries-image-dataset' desde Hugging Face...")
        # Load the test split (smaller and containing query/product relevance evaluations)
        dataset = load_dataset("crossingminds/shopping-queries-image-dataset", split="train", streaming=True)
        
        # Pull a subset of rows
        records = []
        iterator = iter(dataset)
        for i in range(SUBSET_SIZE):
            try:
                row = next(iterator)
                records.append(row)
            except StopIteration:
                break
        
        print(f"Descargados {len(records)} registros de consultas-productos.")
        
        # Build Corpus of Products
        # Each unique product should have: product_id, title, image_url
        products = {}
        # Build Qrels list of Query-Product relevance pairs
        # Each query should have: query_id, query_text, product_id, relevance (esci_label)
        qrels_data = {}
        
        for rec in records:
            p_id = rec.get("product_id")
            # Try multiple possible field names for product title
            p_title = (
                rec.get("product_title") or
                rec.get("title") or
                rec.get("product_name") or
                rec.get("name") or
                ""
            )
            # Skip products with no real title (generic "Product XXXX")
            if not p_title or p_title.strip() == "" or p_title == f"Product {p_id}":
                p_title = None  # Mark as invalid, will skip below

            # Map standard placeholder or scraped image url
            p_image = rec.get("image_url") or rec.get("product_image_url") or "https://via.placeholder.com/150?text=No+Image"
            
            if p_id and p_title:
                products[p_id] = {
                    "product_id": p_id,
                    "title": p_title,
                    "image_url": p_image
                }
            
            q_id = rec.get("query_id")
            q_text = rec.get("query")
            label = rec.get("esci_label") # Exact, Substitute, Complement, Irrelevant
            
            # Map ESCI label to a numeric relevance score for NDCG evaluation
            # Exact = 3, Substitute = 2, Complement = 1, Irrelevant = 0
            relevance_map = {"Exact": 3, "Substitute": 2, "Complement": 1, "Irrelevant": 0}
            rel_score = relevance_map.get(label, 0)
            
            if q_id and q_text and p_id and p_id in products:
                if q_id not in qrels_data:
                    qrels_data[q_id] = {
                        "query_id": q_id,
                        "query": q_text,
                        "relevance": []
                    }
                qrels_data[q_id]["relevance"].append({
                    "product_id": p_id,
                    "score": rel_score,
                    "label": label
                })

        corpus_list = list(products.values())
        
        # If no valid titles were found, fall back to mock corpus
        if len(corpus_list) == 0:
            print("No se encontraron títulos válidos en el dataset. Usando corpus mock de demostración.")
            generate_mock_corpus()
            return
        with open(CORPUS_PATH, "w", encoding="utf-8") as f:
            json.dump(corpus_list, f, indent=2, ensure_ascii=False)
        print(f"Corpus indexado guardado exitosamente: {len(corpus_list)} productos en {CORPUS_PATH}")

        # Save Qrels
        with open(QRELS_PATH, "w", encoding="utf-8") as f:
            json.dump(list(qrels_data.values()), f, indent=2, ensure_ascii=False)
        print(f"Juicios de relevancia (qrels) guardados exitosamente: {len(qrels_data)} consultas en {QRELS_PATH}")
        
    except Exception as e:
        print(f"Error al descargar desde Hugging Face: {e}")
        print("Generando corpus y qrels simulados para desarrollo local...")
        generate_mock_corpus()

def generate_mock_corpus():
    ensure_dirs()
    # Mock data for e-commerce products
    mock_products = [
        {"product_id": "P001", "title": "Nike Air Zoom Running Shoes Blue", "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"},
        {"product_id": "P002", "title": "Adidas Ultraboost White Sneakers", "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400"},
        {"product_id": "P003", "title": "Leather Running Shoes Brown", "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400"},
        {"product_id": "P004", "title": "Minimalist Coffee Mug Ceramic Matte Black", "image_url": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=400"},
        {"product_id": "P005", "title": "Double-walled Glass Espresso Cup Clear", "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400"},
        {"product_id": "P006", "title": "Ergonomic Office Chair Mesh Back Swivel", "image_url": "https://images.unsplash.com/photo-1505797149-43b0069ec26b?w=400"},
        {"product_id": "P007", "title": "Mechanical Keyboard RGB Backlit Brown Switches", "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400"},
        {"product_id": "P008", "title": "Wireless Bluetooth Earbuds Noise Cancelling White", "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400"},
        {"product_id": "P009", "title": "Smart Watch Fitness Tracker Black Strap", "image_url": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=400"},
        {"product_id": "P010", "title": "Leather Wallet Slim RFID Blocking Brown", "image_url": "https://images.unsplash.com/photo-1627124118303-622c97a5c53b?w=400"},
    ]
    
    mock_qrels = [
        {
            "query_id": "Q01",
            "query": "running shoes",
            "relevance": [
                {"product_id": "P001", "score": 3, "label": "Exact"},
                {"product_id": "P002", "score": 3, "label": "Exact"},
                {"product_id": "P003", "score": 2, "label": "Substitute"},
                {"product_id": "P008", "score": 0, "label": "Irrelevant"}
            ]
        },
        {
            "query_id": "Q02",
            "query": "coffee mug",
            "relevance": [
                {"product_id": "P004", "score": 3, "label": "Exact"},
                {"product_id": "P005", "score": 2, "label": "Substitute"},
                {"product_id": "P006", "score": 0, "label": "Irrelevant"}
            ]
        },
        {
            "query_id": "Q03",
            "query": "office keyboard",
            "relevance": [
                {"product_id": "P007", "score": 3, "label": "Exact"},
                {"product_id": "P006", "score": 1, "label": "Complement"},
                {"product_id": "P001", "score": 0, "label": "Irrelevant"}
            ]
        }
    ]
    
    with open(CORPUS_PATH, "w", encoding="utf-8") as f:
        json.dump(mock_products, f, indent=2, ensure_ascii=False)
    with open(QRELS_PATH, "w", encoding="utf-8") as f:
        json.dump(mock_qrels, f, indent=2, ensure_ascii=False)
        
    print(f"Corpus de prueba y qrels creados exitosamente en {DATA_DIR}")

if __name__ == "__main__":
    download_and_prepare_corpus()
