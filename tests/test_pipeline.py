import os

import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "model", "model.joblib")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "housing_data.csv")


def test_dataset_exists_and_has_expected_columns():
    df = pd.read_csv(DATA_PATH)
    expected = {
        "area_sqft", "city", "locality", "bedrooms", "bathrooms",
        "age_years", "furnishing", "parking", "amenities_score", "price",
    }
    assert expected.issubset(df.columns)
    assert len(df) >= 2000
    assert (df["price"] > 0).all()


def test_model_artifact_loads_and_predicts():
    model = joblib.load(MODEL_PATH)
    sample = pd.DataFrame([{
        "area_sqft": 1200,
        "bedrooms": 2,
        "bathrooms": 2,
        "age_years": 5,
        "parking": 1,
        "amenities_score": 6.0,
        "city": "Pune",
        "locality": "Kothrud",
        "furnishing": "Semi-Furnished",
    }])
    pred = model.predict(sample)
    assert pred[0] > 0


def test_prediction_scales_with_area():
    model = joblib.load(MODEL_PATH)

    def make(area):
        return pd.DataFrame([{
            "area_sqft": area,
            "bedrooms": 2,
            "bathrooms": 2,
            "age_years": 5,
            "parking": 1,
            "amenities_score": 6.0,
            "city": "Pune",
            "locality": "Kothrud",
            "furnishing": "Semi-Furnished",
        }])

    small = model.predict(make(600))[0]
    large = model.predict(make(2400))[0]
    assert large > small
