# AI Real Estate Advisor

## Overview
AI Real Estate Advisor is an end-to-end Machine Learning + Generative AI project that predicts Indian residential property prices and generates a natural-language investment insight for each prediction. It ships as two deployable services: a FastAPI model-serving backend and a Streamlit UI.

## Problem Statement
Estimating the fair price of a property is challenging due to multiple influencing factors such as location, size, amenities, and market trends. Buyers and investors often lack accurate price estimation, data-driven insights, and clear investment guidance. This project addresses that with a regression model plus an LLM-generated explanation layer.

## System Workflow

```mermaid
flowchart LR
    A[Streamlit UI] -- property form --> B[FastAPI /predict]
    B -- loads --> C[(model.joblib\nsklearn pipeline)]
    B -- price --> A
    A -- prediction + inputs --> D[FastAPI /insights]
    D -- has OPENAI_API_KEY? --> E[OpenAI-compatible LLM]
    D -- no key --> F[Template explanation]
    E --> A
    F --> A
```

## Features (Implemented)
- Synthetic but realistically-correlated Indian housing dataset generator (`src/generate_data.py`)
- Feature engineering + preprocessing pipeline (`src/preprocessing.py`): scaling for numeric features, one-hot encoding for categoricals
- Model training with candidate comparison via 5-fold CV — RandomForest vs GradientBoosting, best picked automatically (`src/train.py`)
- FastAPI backend with `/predict` and `/insights` endpoints, Pydantic request/response validation (`app/`)
- LLM-backed insight generation (OpenAI-compatible client) with a graceful template fallback when `OPENAI_API_KEY` is unset
- Streamlit frontend with a property form, predicted price, AI insight, and a market-comparison chart against similar listings
- Pytest suite covering the ML pipeline and the API (`tests/`)
- Deploy-ready config for Render/Railway (backend) and Streamlit Community Cloud (frontend)

### Future Enhancements (GenAI)
- Chat-based real estate assistant
- Retrieval-augmented market trend analysis over historical listings
- Multi-city comparison and rent-vs-buy analysis

## Tech Stack

**Core**: Python, Pandas, NumPy, Scikit-learn, Joblib
**Visualization**: Matplotlib
**Backend**: FastAPI, Pydantic, Uvicorn
**Frontend**: Streamlit
**GenAI**: OpenAI-compatible chat completion API

## Project Structure

```
ai-real-estate-advisor/
├── data/                  housing_data.csv (synthetic, generated)
├── notebooks/             exploratory notebooks (optional, ad hoc)
├── src/                   generate_data.py, preprocessing.py, train.py
├── app/                   main.py (FastAPI), schemas.py, insights.py, streamlit_app.py, model/
├── tests/                 pytest suite (pipeline + API)
├── docs/                  DEPLOYMENT.md
├── render.yaml, Procfile, runtime.txt   deploy configs
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Setup
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # then optionally add OPENAI_API_KEY
```

### 2. Generate data & train the model
```bash
python src/generate_data.py   # writes data/housing_data.csv
python src/train.py           # writes app/model/model.joblib + metrics.json
```

### 3. Run the API
```bash
uvicorn app.main:app --reload
```
Docs at http://localhost:8000/docs — try `/predict` and `/insights`.

### 4. Run the frontend
```bash
streamlit run app/streamlit_app.py
```
Set `API_BASE_URL` (defaults to `http://localhost:8000`) if the backend runs elsewhere.

### 5. Run tests
```bash
pytest -q
```

## Example Use Case

Input: Area 1200 sqft, Pune, Kothrud, 2BHK, 2 bath, 5 years old, semi-furnished, 1 parking, amenities 6/10

Output: Predicted Price ≈ ₹95.8 Lakh (GradientBoostingRegressor)

AI Insight (template mode, no API key): "This 2BHK in Kothrud, Pune is estimated at ₹85.0 Lakh (~₹7,083/sqft)... Buyers should independently verify recent local transactions and factor in maintenance costs before deciding."

## Model Notes
Trained on a synthetic 4,000-row dataset spanning 7 Indian cities with engineered correlations between area, bedrooms, amenities, age and price. Gradient Boosting was selected over Random Forest via 5-fold CV (R² ≈ 0.95 on held-out test data). Since the data is synthetic, absolute prices are illustrative, not real market figures — see `docs/DEPLOYMENT.md` for how to swap in a real dataset.

## Deployment
See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for deploying the backend to Render/Railway and the frontend to Streamlit Community Cloud.

## Screenshots
_(placeholder — add UI screenshots here once deployed, e.g. `docs/screenshots/form.png`, `docs/screenshots/prediction.png`)_

## Learning Journey
This project is part of my journey to transition into Machine Learning and Generative AI by building real-world projects step by step.

## Contributions
This is a personal learning project, but suggestions and feedback are welcome.
