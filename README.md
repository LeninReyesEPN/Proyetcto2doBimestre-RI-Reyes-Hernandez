# Sistema de Recuperación de Información Multimodal con RAG

Este proyecto implementa un sistema completo de **Recuperación de Información Multimodal** basado en **RAG (Retrieval-Augmented Generation)** utilizando **CLIP** para la generación de embeddings multimodales, **FAISS** para la indexación y búsqueda vectorial rápida, y la **API de Google Gemini** como modelo de lenguaje generativo.

Fue desarrollado para la asignatura de Recuperación de Información en la Escuela Politécnica Nacional (EPN).

---

## 🎨 Características del Sistema

### 1. Interfaz Web Conversacional (Frontend Next.js)
* Estética monocromática minimalista de alto contraste (negro absoluto y blanco).
* Fuente tipográfica **Josefin Sans** aplicada de forma global en todo el DOM.
* **Visualización de Evidencias (Requisito Crítico)**: Cada respuesta del asistente incluye un panel colapsable que muestra las evidencias utilizadas por el RAG (título del producto, imagen previsualizada, ID del producto y similitud coseno exacta).

### 2. Pipeline Multimodal y RAG (Backend FastAPI)
* **Embeddings Multimodales reales**: cada producto se indexa con la fusión de su embedding de **texto** (título) y su embedding de **imagen** (descargada y codificada con la torre visual de `clip-ViT-B-32`); si la imagen no se puede descargar, se indexa solo con texto. La consulta del usuario se codifica solo como texto. Detalle en `INFORME.pdf` (Sección 2) y `backend/embeddings.py` / `backend/vector_db.py`.
* **Corpus Real**: une dos datasets de Hugging Face — `crossingminds/shopping-queries-image-dataset` (SQID, imágenes reales de producto) con `tasksource/esci` (consultas, títulos y juicios de relevancia ESCI, filtrado a `locale=us` y `small_version=1`) — conservando solo productos con imagen real asociada. Ver `INFORME.pdf` para el detalle completo y `backend/corpus.py` para la implementación. Si no hay conexión a internet, cae automáticamente a un corpus mock de 10 productos para desarrollo local.
* **Base de Datos Vectorial**: Indexa los vectores de productos y realiza la recuperación por similitud coseno con **FAISS**.

### 3. Funcionalidades de Excelencia (+60 Puntos Extra)
* **Re-ranking (+15 pts)**: Reordena las evidencias recuperadas usando el modelo Cross-Encoder `ms-marco-MiniLM-L-6-v2`.
* **Query Expansion (+15 pts)**: Expansión y reformulación automática de consultas usando Gemini.
* **Relevance Feedback (+15 pts)**: Al pulsar "Me gusta" o "No me gusta" en el chat, el sistema guarda la interacción y ajusta los scores de relevancia para búsquedas futuras.
* **Memoria Conversacional (+15 pts)**: Mantiene el contexto de los últimos turnos de conversación e historial en cada petición de RAG.

### 4. Módulo de Evaluación Experimental
* Computa de forma automática métricas de calidad en base a los juicios de relevancia (`esci_label`) del dataset ESCI, comparando el ranking baseline (solo CLIP+FAISS) contra el ranking con Re-ranking (Cross-Encoder) aplicado:
  * **Precision@k** (para k=1, 3, 5)
  * **Recall@k** (para k=1, 3, 5)
  * **NDCG@k** (para k=1, 3, 5)
* `GET /api/evaluate` devuelve ambas variantes en `metrics.baseline_faiss` y `metrics.with_reranking`.

---

## ⚙️ Estructura del Código

```bash
├── backend/
│   ├── corpus.py         # Descarga y procesa el corpus de Hugging Face
│   ├── embeddings.py     # Genera vectores usando el modelo CLIP (texto e imagen)
│   ├── vector_db.py      # Controla el índice FAISS local
│   ├── rag.py            # Orquestador RAG (LLM, re-ranking, query expansion, feedback)
│   ├── evaluation.py     # Ejecuta la evaluación experimental de métricas (Precision, Recall, NDCG)
│   ├── main.py           # Servidor REST de FastAPI
│   ├── requirements.txt  # Dependencias de Python del backend
│   └── test_pipeline.py  # Prueba end-to-end del pipeline completo (corpus, índice, RAG, evaluación)
├── src/                  # Código fuente del Frontend Next.js (TypeScript/React)
│   ├── app/              # Enrutador App Router (page.tsx, globals.css, layout.tsx)
│   └── components/       # Componentes visuales (chat-area.tsx, sidebar.tsx)
```

---

## 🚀 Instalación y Ejecución

### Requisitos Previos
* Python 3.9+ instalado.
* Node.js 18+ y npm instalados.
* Clave de API de Gemini (debes exportarla como variable de entorno `GEMINI_API_KEY`).
* Conexión a internet estable en la primera ejecución: se necesita para descargar los datasets de Hugging Face (SQID y ESCI), los pesos de los modelos `clip-ViT-B-32` y `cross-encoder/ms-marco-MiniLM-L-6-v2` (~700MB en total), y las imágenes de producto desde el CDN de Amazon. Sin conexión, el sistema cae automáticamente a un corpus mock de 10 productos.

### Paso 1: Configurar y Ejecutar el Backend (Python)

1. Inicializa el entorno virtual de Python:
   ```bash
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   ```
2. Instala las dependencias utilizando el archivo `requirements.txt`:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Exporta tu clave de API de Gemini:
   ```bash
   export GEMINI_API_KEY="tu-api-key-aqui"
   ```
4. Corre el servidor FastAPI:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
   * *Nota: En la primera ejecución, el servidor descargará el corpus de Hugging Face y construirá el índice FAISS automáticamente — incluyendo la descarga de las imágenes de producto y la generación de sus embeddings visuales con CLIP. Las imágenes se descargan en paralelo (16 hilos) pero se codifican **una por una** (`backend/embeddings.py`), una medida de seguridad para evitar un SegFault de PyTorch/CLIP observado en macOS al codificar lotes de imágenes. Con el corpus real (~350 productos) esto puede tardar entre 3 y 8 minutos, más 1-5 min extra si es la primera vez que se descargan los modelos CLIP/Cross-Encoder en esta máquina (~700MB). Arranques posteriores son casi instantáneos porque el corpus y el índice quedan cacheados en `backend/data/`.*

### Paso 2: Configurar y Ejecutar el Frontend (Next.js)

1. En la raíz del proyecto, instala los paquetes npm:
   ```bash
   npm install
   ```
2. Ejecuta el servidor de desarrollo del frontend:
   ```bash
   npm run dev
   ```
3. Abre tu navegador e ingresa a **[http://localhost:3000](http://localhost:3000)**.

---

## 📊 Evaluación Experimental & Pruebas Locales

Para ejecutar las pruebas y evaluar las métricas de Precision, Recall y NDCG contra los juicios de relevancia del benchmark de la EPN:

1. **Prueba de Pipeline Completo**: Corre el pipeline completo localmente (indexación, búsqueda RAG y métricas):
   ```bash
   python backend/test_pipeline.py
   ```
2. **Endpoint de FastAPI**: Llama al endpoint de evaluación desde tu terminal con `curl`:
   ```bash
   curl http://localhost:8000/api/evaluate
   ```
3. **Módulo Python**: Ejecuta directamente el módulo de métricas:
   ```bash
   python -m backend.evaluation
   ```
   Esto imprimirá dos tablas de métricas promedio para `K=1`, `K=3` y `K=5`: el ranking baseline (solo CLIP+FAISS) y el ranking con Re-ranking (Cross-Encoder) aplicado.

---

## 📄 Informe Técnico (PDF)

El informe técnico (corpus, arquitectura, pipeline, resultados experimentales y funcionalidades de excelencia) está en `INFORME.pdf`, con un máximo de 5 páginas según lo solicitado.
