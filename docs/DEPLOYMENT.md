# Deployment Guide

Two independent services are deployed separately: the FastAPI backend and the Streamlit frontend.

## 1. Backend (FastAPI) → Render

Config files already in the repo root: `render.yaml`, `Procfile`, `runtime.txt`.

Steps:
1. Push this repo to GitHub.
2. In Render, choose **New → Blueprint** and point it at the repo (it will read `render.yaml`), or create a **New Web Service** manually with:
   - Build command: `pip install -r requirements.txt && python src/train.py`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set the environment variable `OPENAI_API_KEY` in the Render dashboard (leave unset to run in template-fallback mode for `/insights`).
4. Deploy. Note the public URL, e.g. `https://ai-real-estate-advisor-api.onrender.com`.

Railway alternative: same build/start commands work with `railway.json`/`Procfile`-style deploys — create a new project, link the repo, set the same commands and env var.

## 2. Frontend (Streamlit) → Streamlit Community Cloud

1. Push this repo to GitHub (same repo is fine).
2. Go to https://share.streamlit.io, click **New app**, select the repo/branch and set the main file path to `app/streamlit_app.py`.
3. Under **Advanced settings → Secrets**, add:
   ```toml
   API_BASE_URL = "https://ai-real-estate-advisor-api.onrender.com"
   ```
4. Deploy. Streamlit Cloud installs from `requirements.txt` automatically.

## Local verification before deploying

```bash
python src/train.py                 # trains model, writes app/model/model.joblib
pytest -q                           # runs the test suite
uvicorn app.main:app --reload       # backend on :8000
streamlit run app/streamlit_app.py  # frontend on :8501
```

## Notes
- The model artifact (`app/model/model.joblib`) is produced by the Render build step directly from `data/housing_data.csv`, so no large binary needs to be committed for deployment to work, though committing it is also fine for a small model like this.
- `/insights` degrades gracefully to a template response when `OPENAI_API_KEY` is not set — useful for a free-tier deploy with no LLM spend.
