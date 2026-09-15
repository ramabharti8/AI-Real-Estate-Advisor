"""Synthetic Indian real-estate dataset generator.

Produces data/housing_data.csv with realistic correlations between
area, location, amenities, age and price so a regression model has
actual signal to learn (not pure noise).
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N_ROWS = 4000

# city -> (base price per sqft in INR, locality list, tier multiplier range)
CITIES = {
    "Mumbai": (18000, ["Andheri", "Bandra", "Powai", "Thane", "Borivali"]),
    "Delhi": (14000, ["Dwarka", "Rohini", "Saket", "Vasant Kunj", "Karol Bagh"]),
    "Bangalore": (9500, ["Whitefield", "Koramangala", "Indiranagar", "HSR Layout", "Electronic City"]),
    "Pune": (7500, ["Hinjewadi", "Kothrud", "Wakad", "Viman Nagar", "Baner"]),
    "Hyderabad": (6800, ["Gachibowli", "Madhapur", "Kondapur", "Kukatpally", "Banjara Hills"]),
    "Chennai": (7200, ["Adyar", "OMR", "Velachery", "Anna Nagar", "T Nagar"]),
    "Ahmedabad": (5200, ["Satellite", "Bopal", "Vastrapur", "Maninagar", "SG Highway"]),
}

FURNISHING = ["Unfurnished", "Semi-Furnished", "Fully-Furnished"]
FURNISHING_PREMIUM = {"Unfurnished": 0.0, "Semi-Furnished": 0.05, "Fully-Furnished": 0.12}


def generate():
    cities = list(CITIES.keys())
    rows = []
    for _ in range(N_ROWS):
        city = RNG.choice(cities)
        base_psf, localities = CITIES[city]
        locality = RNG.choice(localities)

        bedrooms = int(RNG.choice([1, 2, 2, 3, 3, 3, 4, 4, 5], p=None))
        # area correlates with bedrooms
        area_sqft = max(300, RNG.normal(bedrooms * 380 + 250, 180))
        bathrooms = max(1, min(bedrooms, int(round(bedrooms * RNG.uniform(0.6, 1.0)))))
        age_years = max(0, int(RNG.exponential(6)))
        age_years = min(age_years, 40)
        furnishing = RNG.choice(FURNISHING, p=[0.45, 0.35, 0.20])
        parking = int(RNG.choice([0, 1, 1, 2], p=[0.15, 0.45, 0.3, 0.10]))
        amenities_score = round(float(np.clip(RNG.normal(6, 2), 0, 10)), 1)

        price_per_sqft = base_psf * RNG.uniform(0.85, 1.15)
        age_depreciation = max(0.55, 1 - age_years * 0.012)
        amenities_premium = 1 + (amenities_score / 10) * 0.18
        furnishing_premium = 1 + FURNISHING_PREMIUM[furnishing]
        parking_premium = 1 + parking * 0.03
        bathroom_premium = 1 + max(0, bathrooms - bedrooms) * 0.02

        price = (
            area_sqft
            * price_per_sqft
            * age_depreciation
            * amenities_premium
            * furnishing_premium
            * parking_premium
            * bathroom_premium
        )
        price *= RNG.normal(1.0, 0.06)  # noise
        price = max(500000, round(price, -3))

        rows.append(
            {
                "area_sqft": round(area_sqft, 1),
                "city": city,
                "locality": locality,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "age_years": age_years,
                "furnishing": furnishing,
                "parking": parking,
                "amenities_score": amenities_score,
                "price": price,
            }
        )

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    df = generate()
    out_path = "data/housing_data.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    print(df.describe(include="all"))
