import os
import sys

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from insights import generate_insight  # noqa: E402
from preprocessing import CATEGORICAL_FEATURES, NUMERIC_FEATURES  # noqa: E402
from schemas import (  # noqa: E402
    InsightRequest,
    InsightResponse,
    MarketSummaryResponse,
    PredictRequest,
    PredictResponse,
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "model.joblib")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "housing_data.csv")

app = FastAPI(title="AI Real Estate Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from rag import router as rag_router  # noqa: E402

app.include_router(rag_router)

_market_cache = None


def _load_market_data():
    global _market_cache
    if _market_cache is None and os.path.exists(DATA_PATH):
        _market_cache = pd.read_csv(DATA_PATH)
    return _market_cache

_model = None
_model_name = "unknown"


def get_model():
    global _model, _model_name
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(
                status_code=503,
                detail="Model artifact not found. Run `python src/train.py` first.",
            )
        _model = joblib.load(MODEL_PATH)
        _model_name = type(_model.named_steps["model"]).__name__
    return _model


@app.get("/")
def root():
    return {"service": "AI Real Estate Advisor API", "status": "ok"}


@app.get("/health")
def health():
    model_ready = os.path.exists(MODEL_PATH)
    return {"status": "ok", "model_ready": model_ready}


def _to_frame(req: PredictRequest) -> pd.DataFrame:
    row = {f: getattr(req, f) for f in NUMERIC_FEATURES + CATEGORICAL_FEATURES}
    return pd.DataFrame([row])


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    model = get_model()
    try:
        X = _to_frame(req)
        price = float(model.predict(X)[0])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    price = max(price, 0)
    lakh = price / 100000
    formatted = f"₹{lakh / 100:.2f} Cr" if lakh >= 100 else f"₹{lakh:.1f} Lakh"

    return PredictResponse(
        predicted_price=round(price, 2),
        predicted_price_formatted=formatted,
        model_name=_model_name,
    )


@app.post("/insights", response_model=InsightResponse)
def insights(req: InsightRequest):
    text, source = generate_insight(req)
    return InsightResponse(insight=text, source=source)


@app.get("/market/summary", response_model=MarketSummaryResponse)
def market_summary():
    data = _load_market_data()
    if data is None:
        raise HTTPException(status_code=503, detail="Dataset not found. Run `python src/generate_data.py` first.")

    avg_by_city = (data.groupby("city")["price"].mean() / 100000).round(2).to_dict()
    by_furnishing = {
        f: (data[data["furnishing"] == f]["price"] / 100000).round(2).tolist()
        for f in data["furnishing"].unique()
    }
    return MarketSummaryResponse(
        listings=len(data),
        median_price=float(data["price"].median()),
        median_area_sqft=float(data["area_sqft"].median()),
        cities_covered=int(data["city"].nunique()),
        avg_price_by_city=avg_by_city,
        price_by_furnishing=by_furnishing,
    )


@app.get("/market/by-city/{city}")
def market_by_city(city: str):
    data = _load_market_data()
    if data is None:
        raise HTTPException(status_code=503, detail="Dataset not found. Run `python src/generate_data.py` first.")

    subset = data[data["city"] == city]
    if subset.empty:
        raise HTTPException(status_code=404, detail=f"No data for city '{city}'")

    top_locality = subset.groupby("locality")["price"].mean().idxmax()
    return {
        "city": city,
        "listings": int(len(subset)),
        "median_price": float(subset["price"].median()),
        "median_price_per_sqft": float((subset["price"] / subset["area_sqft"]).median()),
        "top_locality": top_locality,
    }
