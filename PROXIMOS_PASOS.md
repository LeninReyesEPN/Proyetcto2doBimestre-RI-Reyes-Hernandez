# Próximos pasos: verificar la ejecución real del proyecto

Este archivo es para ti (o para tu agente de Claude Code) al abrir este repo por primera vez después del `git pull`. Contexto breve: el proyecto tenía un bug donde el sistema indexaba un **corpus mock de 10 productos falsos** en vez del dataset real, y las métricas del informe eran inventadas. Ya se corrigió el código (nuevo `backend/corpus.py`, embeddings de imagen reales en `backend/vector_db.py`/`embeddings.py`, `evaluation.py` con comparación baseline vs re-ranking), pero **nadie ha corrido el pipeline completo todavía** — se necesita una ejecución real en una máquina con memoria suficiente para: (1) confirmar que todo funciona sin errores, (2) obtener las métricas reales para `INFORME.md`, (3) regenerar `INFORME.pdf`.

Sigue estos pasos en orden y anota el resultado de cada uno.

---

## Paso 0 — Traer los cambios

```bash
git pull origin main
```

Si tienes cambios locales sin commitear que choquen, avisa antes de continuar (no hagas `git reset --hard` sin preguntar).

## Paso 1 — Limpiar caché local vieja (IMPORTANTE)

`backend/data/` está en `.gitignore`, así que el `pull` **no la toca**. Si ya habías corrido el proyecto antes, ahí sigue el corpus mock viejo, y el código nuevo lo detecta y se lo salta (nunca descarga el real). Bórralo:

```bash
rm -f backend/data/corpus.json backend/data/qrels.json backend/data/faiss.index backend/data/faiss.index.map
```

(`backend/data/feedback.json`, si existe, no hace falta borrarlo — es inofensivo.)

## Paso 2 — Entorno Python

```bash
cd backend
python3 -m venv .venv          # solo si .venv no existe aún
source .venv/bin/activate
pip install -r requirements.txt   # se agregó "pillow" como dependencia nueva
cd ..
```

## Paso 3 — Clave de API de Gemini

```bash
export GEMINI_API_KEY="tu-api-key-aqui"
```

Sin esto, la expansión de consulta y la generación de respuesta van a fallar (con degradación controlada, no un crash), así que ponla antes de probar el chat.

## Paso 4 — Construir el corpus real (con logs guardados)

```bash
python -m backend.corpus 2>&1 | tee setup_corpus.log
```

**Qué esperar:** líneas como `Corpus indexado guardado exitosamente: N productos en ...` y `Juicios de relevancia (qrels) guardados exitosamente: M consultas en ...`, con N y M mayores a 0.

**Señal de alerta:** si ves `Usando corpus mock de demostración` o `Error al descargar/construir el corpus real: ...`, algo falló (red, cambio en el dataset de Hugging Face, etc.). Comparte el contenido completo de `setup_corpus.log` para que lo revisemos.

Puede tardar entre 30 segundos y un par de minutos (depende de la red y de cuántas filas del dataset ESCI hay que escanear hasta reunir ~25 consultas con imagen real).

## Paso 5 — Construir el índice FAISS (con embeddings de imagen)

```bash
python -m backend.vector_db 2>&1 | tee setup_index.log
```

**Qué esperar:**
- `Generando embeddings visuales con CLIP para N imágenes de producto...`
- `Embeddings multimodales (texto+imagen) generados para X/N productos (...)` — X debería ser mayor a 0 (si es 0, ninguna imagen se pudo descargar, revisar conexión a internet).
- `Indexación completada. N productos guardados en ...`
- Al final, un `Test Search Results: [...]` con productos reales (no "Nike Air Zoom..." del mock viejo).

La primera vez, esto también descarga los pesos de CLIP (~600MB) y puede tardar varios minutos extra solo por eso.

## Paso 6 — Evaluación experimental (esto es lo que necesito)

```bash
python -m backend.evaluation 2>&1 | tee setup_evaluation.log
```

Esto imprime **dos** tablas JSON: `Baseline: solo CLIP + FAISS` y `Con Re-ranking (Cross-Encoder)`, cada una con Precision@k, Recall@k y NDCG@k para k=1,3,5.

➡️ **Copia esos dos bloques de números** (o el archivo `setup_evaluation.log` completo) — con eso lleno las Tablas A y B de `INFORME.md` (están marcadas `_pendiente_`).

## Paso 7 — Probar el sistema completo (backend + frontend)

Terminal 1:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2:
```bash
npm install     # solo si no lo has corrido antes
npm run dev
```

Abre `http://localhost:3000` y prueba:
- Escribe una consulta relacionada con algún producto real del nuevo corpus (revisa `backend/data/qrels.json` para ver ejemplos de consultas reales — ya no son "running shoes" / "coffee mug" del mock).
- Confirma que aparece una respuesta y el panel de "Evidencias Multimodales" con imágenes, ID de producto y % de similitud.
- Prueba los botones de "me gusta"/"no me gusta" (tanto los del mensaje como los de cada evidencia) y confirma que no salen errores en la consola del navegador.

## Paso 8 — Completar el informe y regenerar el PDF

1. Abre `INFORME.md`, sección 4, y reemplaza los `_pendiente_` de la Tabla A y Tabla B con los números del Paso 6.
2. Regenera el PDF:
   ```bash
   python3 generate_pdf.py
   ```
3. Abre `INFORME.pdf` y cuenta las páginas — el enunciado exige **máximo 5 páginas**. Si se pasa, avisa para recortar texto (probablemente la Sección 1 o la guía de análisis de la Sección 4).

## Paso 9 — Commit y push

```bash
git add INFORME.md INFORME.pdf
git commit -m "docs: completar métricas reales de evaluación en el informe"
git push origin main
```

(No hace falta subir los `.log` — son solo para compartir conmigo si algo falla en algún paso.)

---

## Si algo falla

En cualquier paso, si ves un error o un resultado inesperado (N=0 productos, corpus mock en vez de real, excepción en la consola, etc.), guarda el mensaje completo y el `.log` correspondiente y compártelo — con eso puedo diagnosticar y corregir el código sin necesidad de adivinar qué pasó.
