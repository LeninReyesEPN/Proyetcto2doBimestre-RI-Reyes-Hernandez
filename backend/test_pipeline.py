import os
import sys

# Add root folder to sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.corpus import download_and_prepare_corpus
from backend.vector_db import build_index, search
from backend.evaluation import run_evaluation
from backend.rag import generate_rag_response

def run_tests():
    print("=== INICIANDO PRUEBAS DE PIPELINE RAG MULTIMODAL ===")
    
    # 1. Test corpus download
    print("\n1. Probando descarga y procesamiento de corpus...")
    download_and_prepare_corpus()
    
    # 2. Test vector indexing
    print("\n2. Probando indexación de vectores (FAISS)...")
    build_index()
    
    # 3. Test vector search
    print("\n3. Probando búsqueda vectorial...")
    results = search("shoes", top_k=2)
    print("Resultados de búsqueda:")
    for r in results:
        print(f"- {r['title']} (ID: {r['product_id']}, Similitud: {r['similarity']*100:.1f}%)")
        
    # 4. Test RAG Response
    print("\n4. Probando pipeline RAG...")
    # Mock some chat history
    history = [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "¡Hola! ¿En qué puedo ayudarte?"}
    ]
    rag_res = generate_rag_response("zapato de correr", history)
    print("Respuesta RAG Generada:")
    print(rag_res["answer"])
    print("\nEvidencias utilizadas:")
    for ev in rag_res["evidences"]:
        print(f"- {ev['title']} (Similitud: {ev['similarity']*100:.1f}%)")

    # 5. Test experimental evaluation
    print("\n5. Probando evaluación experimental...")
    run_evaluation()
    
    print("\n=== PRUEBAS COMPLETADAS CON ÉXITO ===")

if __name__ == "__main__":
    run_tests()
