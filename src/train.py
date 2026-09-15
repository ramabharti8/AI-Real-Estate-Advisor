"""Train, cross-validate, and persist the house-price regression model.

Re-runnable: `python src/train.py` regenerates model.joblib and metrics.json.
"""
import json
import os

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from preprocessing import build_pipeline, load_dataset

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "housing_data.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "model")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

CANDIDATES = {
    "random_forest": RandomForestRegressor(n_estimators=300, max_depth=None, min_samples_leaf=2, random_state=42, n_jobs=-1),
    "gradient_boosting": GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=3, random_state=42),
}


def main():
    ds = load_dataset(DATA_PATH)
    X_train, X_test, y_train, y_test = train_test_split(ds.X, ds.y, test_size=0.2, random_state=42)

    best_name, best_pipeline, best_cv_score = None, None, -np.inf
    cv_results = {}
    for name, model in CANDIDATES.items():
        pipeline = build_pipeline(model)
        scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)
        cv_results[name] = {"mean_r2": float(scores.mean()), "std_r2": float(scores.std())}
        print(f"{name}: CV R2 = {scores.mean():.4f} (+/- {scores.std():.4f})")
        if scores.mean() > best_cv_score:
            best_cv_score = scores.mean()
            best_name = name
            best_pipeline = pipeline

    best_pipeline.fit(X_train, y_train)
    preds = best_pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = r2_score(y_test, preds)

    print(f"\nSelected model: {best_name}")
    print(f"Test MAE:  {mae:,.0f}")
    print(f"Test RMSE: {rmse:,.0f}")
    print(f"Test R2:   {r2:.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_PATH)

    metrics = {
        "selected_model": best_name,
        "cv_results": cv_results,
        "test_mae": mae,
        "test_rmse": rmse,
        "test_r2": r2,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved metrics -> {METRICS_PATH}")


if __name__ == "__main__":
    main()
