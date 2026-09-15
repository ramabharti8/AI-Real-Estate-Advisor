"""Feature engineering & preprocessing shared by training and inference."""
from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = ["area_sqft", "bedrooms", "bathrooms", "age_years", "parking", "amenities_score"]
CATEGORICAL_FEATURES = ["city", "locality", "furnishing"]
TARGET = "price"


@dataclass
class Dataset:
    X: pd.DataFrame
    y: pd.Series


def load_dataset(csv_path: str) -> Dataset:
    df = pd.read_csv(csv_path)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]
    return Dataset(X=X, y=y)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )


def build_pipeline(model) -> Pipeline:
    return Pipeline(steps=[("preprocess", build_preprocessor()), ("model", model)])
