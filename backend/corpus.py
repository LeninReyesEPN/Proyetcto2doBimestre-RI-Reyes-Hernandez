import os
import json
from datasets import load_dataset

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CORPUS_PATH = os.path.join(DATA_DIR, "corpus.json")
QRELS_PATH = os.path.join(DATA_DIR, "qrels.json")

# Dataset de imágenes reales de producto (Shopping Queries Image Dataset - SQID).
# Solo trae product_id + image_url; no incluye título, consulta ni esci_label.
IMAGE_DATASET = "crossingminds/shopping-queries-image-dataset"
IMAGE_DATASET_CONFIG = "product_image_urls"

# Dataset de texto (Amazon Shopping Queries Dataset - ESCI): trae la consulta,
# el título del producto y el juicio de relevancia (esci_label) que SQID no incluye.
TEXT_DATASET = "tasksource/esci"
TEXT_DATASET_SPLIT = "test"

# Filtramos al locale 'us' y a la "small_version" (el subconjunto curado que usa
# el paper original de ESCI para benchmarking) para mantener un corpus manejable.
PRODUCT_LOCALE = "us"

# Número objetivo de consultas distintas a incluir en el corpus/qrels.
NUM_QUERIES = 25
# Límite de filas del stream de ESCI a inspeccionar antes de detenerse (salvaguarda).
MAX_SCAN_ROWS = 150000

# Mapeo de la etiqueta ESCI a un puntaje de relevancia graduado para NDCG.
RELEVANCE_MAP = {"Exact": 3, "Substitute": 2, "Complement": 1, "Irrelevant": 0}


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
        # 1. Cargar las URLs de imágenes reales de producto desde SQID.
        #    El config 'product_image_urls' es pequeño (~165k filas) y se carga completo en memoria.
        print(f"Cargando imágenes reales de producto desde '{IMAGE_DATASET}' ({IMAGE_DATASET_CONFIG})...")
        image_ds = load_dataset(IMAGE_DATASET, IMAGE_DATASET_CONFIG, split="train")
        image_map = {
            row["product_id"]: row["image_url"]
            for row in image_ds
            if row.get("image_url")
        }
        print(f"Imágenes de producto disponibles: {len(image_map)}.")

        # 2. Transmitir (streaming) el dataset ESCI para obtener consulta, título del
        #    producto y juicio de relevancia, uniéndolo con el mapa de imágenes por product_id.
        print(f"Transmitiendo consultas y juicios de relevancia desde '{TEXT_DATASET}' (split={TEXT_DATASET_SPLIT})...")
        text_ds = load_dataset(TEXT_DATASET, split=TEXT_DATASET_SPLIT, streaming=True)

        products = {}
        qrels_data = {}
        scanned = 0

        for row in text_ds:
            scanned += 1
            if scanned > MAX_SCAN_ROWS:
                print(f"Se alcanzó el límite de escaneo ({MAX_SCAN_ROWS} filas).")
                break

            if row.get("product_locale") != PRODUCT_LOCALE or row.get("small_version") != 1:
                continue

            p_id = row.get("product_id")
            image_url = image_map.get(p_id)
            title = row.get("product_title")

            # Solo indexamos productos que tengan un título válido Y una imagen real
            # asociada: es lo que hace al corpus genuinamente multimodal.
            if not p_id or not image_url or not title:
                continue

            q_id = str(row.get("query_id"))
            # Una vez alcanzado el número objetivo de consultas distintas, ya no se
            # aceptan consultas nuevas (pero sí se completan las relevancias de las existentes).
            if q_id not in qrels_data and len(qrels_data) >= NUM_QUERIES:
                continue

            label = row.get("esci_label")
            rel_score = RELEVANCE_MAP.get(label, 0)

            products[p_id] = {"product_id": p_id, "title": title, "image_url": image_url}

            qrels_data.setdefault(q_id, {
                "query_id": q_id,
                "query": row.get("query"),
                "relevance": []
            })
            qrels_data[q_id]["relevance"].append({
                "product_id": p_id,
                "score": rel_score,
                "label": label
            })

        print(f"Filas escaneadas: {scanned}. Consultas candidatas: {len(qrels_data)}.")

        # Descartamos consultas sin ningún producto relevante (score > 0): no aportan
        # señal útil para Precision/Recall/NDCG.
        qrels_data = {
            q_id: q for q_id, q in qrels_data.items()
            if any(item["score"] > 0 for item in q["relevance"])
        }

        corpus_list = list(products.values())

        # Si la unión con Hugging Face no produjo un corpus real utilizable, se usa el mock local.
        if not corpus_list or not qrels_data:
            print("No se pudo construir un corpus real con imágenes asociadas. Usando corpus mock de demostración.")
            generate_mock_corpus()
            return

        with open(CORPUS_PATH, "w", encoding="utf-8") as f:
            json.dump(corpus_list, f, indent=2, ensure_ascii=False)
        print(f"Corpus indexado guardado exitosamente: {len(corpus_list)} productos en {CORPUS_PATH}")

        with open(QRELS_PATH, "w", encoding="utf-8") as f:
            json.dump(list(qrels_data.values()), f, indent=2, ensure_ascii=False)
        print(f"Juicios de relevancia (qrels) guardados exitosamente: {len(qrels_data)} consultas en {QRELS_PATH}")

    except Exception as e:
        print(f"Error al descargar/construir el corpus real: {e}")
        print("Generando corpus y qrels simulados para desarrollo local...")
        generate_mock_corpus()


def generate_mock_corpus():
    """Corpus mock de respaldo, usado solo si la descarga real desde Hugging Face falla
    (por ejemplo, sin conexión a internet)."""
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
