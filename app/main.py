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
from schemas import InsightRequest, InsightResponse, PredictRequest, PredictResponse  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "model.joblib")

app = FastAPI(title="AI Real Estate Advisor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
