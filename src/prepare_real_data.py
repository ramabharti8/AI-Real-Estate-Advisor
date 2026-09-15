"""Convert a real, downloaded housing CSV into the schema src/train.py expects.

Built against Kaggle's "Bengaluru House Price Data" (amitabhajoy/bengaluru-house-price-data),
the most commonly used open Indian housing dataset for this kind of exercise. Its raw columns are:
area_type, availability, location, size, society, total_sqft, bath, balcony, price (in Lakh INR).

That dataset has no age, furnishing, parking or amenities columns, so this script imputes
sensible defaults for those and prints a summary of every assumption it made -- treat the
resulting model's accuracy as lower-confidence on those imputed fields. To use a different
real dataset, adjust RAW_COLUMN_MAP and the parsing helpers below to match its columns.

Usage:
    python src/prepare_real_data.py --input data/raw/Bengaluru_House_Data.csv --city Bangalore
"""
import argparse
import re

import numpy as np
import pandas as pd

from preprocessing import CATEGORICAL_FEATURES, NUMERIC_FEATURES, TARGET

RNG = np.random.default_rng(7)


def parse_sqft(value) -> float:
    """Handles plain numbers, ranges ('2100-2850'), and unit suffixes ('34.46Sq. Meter')."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if "-" in text:
        lo, hi = text.split("-")
        try:
            return (float(lo) + float(hi)) / 2
        except ValueError:
            return np.nan
    match = re.match(r"^([\d.]+)", text)
    if not match:
        return np.nan
    number = float(match.group(1))
    if "sq. meter" in text.lower():
        number *= 10.7639
    elif "perch" in text.lower():
        number *= 272.25
    elif "acre" in text.lower():
        number *= 43560
    elif "cent" in text.lower():
        number *= 435.6
    elif "guntha" in text.lower():
        number *= 1089
    return number


def parse_bedrooms(size_value) -> float:
    if pd.isna(size_value):
        return np.nan
    match = re.match(r"^(\d+)", str(size_value).strip())
    return float(match.group(1)) if match else np.nan


def clean_locality(location_value) -> str:
    if pd.isna(location_value):
        return "Unknown"
    return str(location_value).strip().split(",")[0][:100] or "Unknown"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the raw downloaded CSV")
    parser.add_argument("--output", default="data/housing_data.csv", help="Where to write the cleaned CSV")
    parser.add_argument("--city", default="Bangalore", help="This dataset covers one city; label rows with it")
    args = parser.parse_args()

    raw = pd.read_csv(args.input)
    print(f"Loaded {len(raw)} raw rows from {args.input}")
    print(f"Raw columns: {list(raw.columns)}")

    df = pd.DataFrame()
    df["area_sqft"] = raw["total_sqft"].apply(parse_sqft)
    df["bedrooms"] = raw["size"].apply(parse_bedrooms) if "size" in raw.columns else np.nan
    df["bathrooms"] = pd.to_numeric(raw.get("bath"), errors="coerce")
    df["city"] = args.city
    df["locality"] = raw["location"].apply(clean_locality) if "location" in raw.columns else "Unknown"
    df["price"] = pd.to_numeric(raw.get("price"), errors="coerce") * 100000  # Kaggle price is in Lakh INR

    # Columns this dataset does not provide -- imputed with clearly-documented defaults.
    df["age_years"] = RNG.integers(0, 15, size=len(df))
    df["furnishing"] = RNG.choice(
        ["Unfurnished", "Semi-Furnished", "Fully-Furnished"], size=len(df), p=[0.5, 0.35, 0.15]
    )
    df["parking"] = np.clip(pd.to_numeric(raw.get("balcony"), errors="coerce").fillna(1), 0, 5).astype(int)
    df["amenities_score"] = np.round(RNG.normal(6, 1.5, size=len(df)).clip(0, 10), 1)

    before = len(df)
    df = df.dropna(subset=NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET])
    df = df[(df["area_sqft"] > 100) & (df["area_sqft"] < 20000) & (df["price"] > 100000)]
    df["bedrooms"] = df["bedrooms"].clip(0, 10).astype(int)
    df["bathrooms"] = df["bathrooms"].clip(0, 10).astype(int)
    dropped = before - len(df)

    df.to_csv(args.output, index=False)

    print(f"\nDropped {dropped} rows with missing/invalid required fields.")
    print(f"Wrote {len(df)} cleaned rows to {args.output}")
    print("\nColumns imputed (not present in the source dataset):")
    print("  age_years        -> random 0-14 years (uniform)")
    print("  furnishing       -> random, weighted toward Unfurnished/Semi-Furnished")
    print("  parking          -> derived from 'balcony' count as a rough proxy")
    print("  amenities_score  -> random, centered at 6.0/10")
    print("\nRun `python src/train.py` next to retrain on this data.")


if __name__ == "__main__":
    main()
