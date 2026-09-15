# Deployment Guide

Two independent services are deployed separately: the FastAPI backend (model + RAG) and the React frontend.

## 1. Backend (FastAPI) → Render

Config files already in the repo root: `render.yaml`, `Procfile`, `runtime.txt`.

Steps:
1. Push this repo to GitHub.
2. In Render, choose **New → Blueprint** and point it at the repo (it will read `render.yaml`), or create a **New Web Service** manually with:
   - Build command: `pip install -r requirements.txt && python src/train.py && python src/ingest_documents.py`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set the environment variable `OPENAI_API_KEY` in the Render dashboard (leave unset to run in template-fallback mode for `/insights` and `/documents/chat`).
4. Deploy. Note the public URL, e.g. `https://ai-real-estate-advisor-api.onrender.com`.

Railway alternative: same build/start commands work with `railway.json`/`Procfile`-style deploys — create a new project, link the repo, set the same commands and env var.

**Persistence note:** Render's free/starter instances have an ephemeral filesystem — anything uploaded via `/documents/upload` after deploy is lost on restart. The five sample documents survive because the build step re-runs `ingest_documents.py` from `data/documents/` on every deploy. For durable uploads, add a persistent disk (Render) or see the Cloud Storage volume approach in `docs/handbook.html` §08.

## 2. Frontend (React) → Vercel / Netlify

1. Push this repo to GitHub (same repo is fine).
2. On Vercel or Netlify, create a new project pointed at this repo with:
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `frontend/dist`
3. Set the environment variable `VITE_API_BASE_URL` to your deployed backend URL, e.g. `https://ai-real-estate-advisor-api.onrender.com`.
4. Deploy.

A full step-by-step for deploying to Google Cloud Platform instead (Cloud Run + Cloud Storage/CDN) is in `docs/handbook.html` §08.

## Local verification before deploying

```bash
python src/train.py                 # trains model, writes app/model/model.joblib
python src/ingest_documents.py       # indexes the RAG documents
pytest -q                            # runs the test suite
uvicorn app.main:app --reload        # backend on :8000
cd frontend && npm run build         # confirms the production build succeeds
```

## Notes
- The model artifact (`app/model/model.joblib`) is produced by the Render build step directly from `data/housing_data.csv`, so no large binary needs to be committed for deployment to work, though committing it is also fine for a small model like this.
- `/insights` and `/documents/chat` degrade gracefully to a template/retrieval-only response when `OPENAI_API_KEY` is not set — useful for a free-tier deploy with no LLM spend.
- The `sentence-transformers` local embedding model downloads (~90 MB) on first use if no OpenAI key is set — factor that into cold-start time on a free-tier backend.
