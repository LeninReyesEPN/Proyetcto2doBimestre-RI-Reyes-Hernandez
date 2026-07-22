import os
import json
import numpy as np
from backend.vector_db import search
from backend.rag import get_cross_encoder

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
QRELS_PATH = os.path.join(DATA_DIR, "qrels.json")

def load_qrels():
    if not os.path.exists(QRELS_PATH):
        raise FileNotFoundError(f"No qrels file found at {QRELS_PATH}.")
    with open(QRELS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_metrics_for_query(retrieved_ids: list[str], relevance_list: list[dict], k: int) -> dict:
    """Computes Precision@K, Recall@K, and NDCG@K for a single query."""
    # Build dictionary of product relevance scores for fast lookup
    rel_map = {item["product_id"]: item["score"] for item in relevance_list}
    
    # 1. Relevance indicators (binary for P & R, graded for NDCG)
    # Consider score > 0 as relevant (Substitute, Complement, Exact)
    relevant_retrieved = 0
    actual_relevances = []
    
    for i in range(min(k, len(retrieved_ids))):
        p_id = retrieved_ids[i]
        rel_score = rel_map.get(p_id, 0)
        actual_relevances.append(rel_score)
        if rel_score > 0:
            relevant_retrieved += 1
            
    # Pad actual relevances up to k with 0
    actual_relevances += [0] * (k - len(actual_relevances))
    
    # 2. Precision@K
    precision = relevant_retrieved / k
    
    # 3. Recall@K
    total_relevant = sum(1 for item in relevance_list if item["score"] > 0)
    recall = (relevant_retrieved / total_relevant) if total_relevant > 0 else 0.0
    
    # 4. NDCG@K
    # DCG@K = sum ( (2^rel - 1) / log2(i+2) ) for i from 0 to k-1
    dcg = 0.0
    for i in range(k):
        rel = actual_relevances[i]
        dcg += (2**rel - 1) / np.log2(i + 2)
        
    # IDCG@K: Sort all ground truth relevance scores in descending order and calculate DCG@K
    ideal_relevances = sorted([item["score"] for item in relevance_list], reverse=True)
    # Pad ideal relevances up to k with 0
    ideal_relevances += [0] * (k - len(ideal_relevances))
    
    idcg = 0.0
    for i in range(k):
        rel = ideal_relevances[i]
        idcg += (2**rel - 1) / np.log2(i + 2)
        
    ndcg = (dcg / idcg) if idcg > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "ndcg": ndcg
    }

def rerank_results(query_text: str, candidates: list[dict]) -> list[dict]:
    """Re-rank de excelencia: reordena los candidatos de FAISS con el Cross-Encoder,
    reutilizando el mismo modelo que usa el pipeline RAG en producción (rag.py)."""
    cross_encoder = get_cross_encoder()
    if not cross_encoder or not candidates:
        return candidates
    pairs = [(query_text, item["title"]) for item in candidates]
    scores = cross_encoder.predict(pairs)
    for item, score in zip(candidates, scores):
        item["re_rank_score"] = float(score)
    return sorted(candidates, key=lambda item: item["re_rank_score"], reverse=True)


def run_evaluation(k_values=[1, 3, 5], apply_reranking: bool = False) -> dict:
    """Evaluates all queries in the qrels dataset and returns averaged metrics.

    Si apply_reranking=True, se recupera un pool más amplio de candidatos con
    FAISS y se reordena con el Cross-Encoder antes de recortar a cada k, lo que
    permite comparar el ranking base (solo CLIP+FAISS) contra el ranking con la
    funcionalidad de excelencia de Re-ranking activada.
    """
    qrels = load_qrels()
    if not qrels:
        print("La base de qrels está vacía.")
        return {}

    overall_metrics = {k: {"precision": [], "recall": [], "ndcg": []} for k in k_values}
    max_k = max(k_values)

    print(f"Evaluando {len(qrels)} consultas del benchmark experimental "
          f"({'con' if apply_reranking else 'sin'} re-ranking)...")
    for q_entry in qrels:
        q_text = q_entry["query"]
        relevance_list = q_entry["relevance"]

        # Retrieve maximum required K (un pool más amplio si luego se va a re-rankear)
        pool_size = max_k * 2 if apply_reranking else max_k
        retrieved_results = search(q_text, top_k=pool_size)

        if apply_reranking:
            retrieved_results = rerank_results(q_text, retrieved_results)[:max_k]

        retrieved_ids = [res["product_id"] for res in retrieved_results]

        # Calculate metrics for each k value
        for k in k_values:
            metrics = calculate_metrics_for_query(retrieved_ids, relevance_list, k)
            overall_metrics[k]["precision"].append(metrics["precision"])
            overall_metrics[k]["recall"].append(metrics["recall"])
            overall_metrics[k]["ndcg"].append(metrics["ndcg"])

    # Calculate average values
    report = {}
    for k in k_values:
        report[f"K={k}"] = {
            "Precision@k": round(float(np.mean(overall_metrics[k]["precision"])), 4),
            "Recall@k": round(float(np.mean(overall_metrics[k]["recall"])), 4),
            "NDCG@k": round(float(np.mean(overall_metrics[k]["ndcg"])), 4)
        }

    print("Resultados de la Evaluación Experimental:")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    print("\n=== Baseline: solo CLIP + FAISS ===")
    run_evaluation(apply_reranking=False)
    print("\n=== Con Re-ranking (Cross-Encoder) ===")
    run_evaluation(apply_reranking=True)
