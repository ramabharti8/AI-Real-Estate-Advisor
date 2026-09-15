"""LLM-backed (or templated fallback) natural-language investment insight."""
import os

from schemas import InsightRequest

SYSTEM_PROMPT = (
    "You are a concise, neutral Indian real-estate advisor. Given a property's "
    "attributes and a model's predicted price, write a 3-4 sentence insight covering "
    "whether the price looks reasonable for the area, one standout factor driving it, "
    "and one practical consideration for a buyer/investor. Avoid guarantees or financial advice."
)


def _format_price(price: float) -> str:
    lakh = price / 100000
    if lakh >= 100:
        return f"₹{lakh / 100:.2f} Cr"
    return f"₹{lakh:.1f} Lakh"


def _template_insight(req: InsightRequest) -> str:
    price_str = _format_price(req.predicted_price)
    per_sqft = req.predicted_price / req.area_sqft
    return (
        f"This {req.bedrooms}BHK in {req.locality}, {req.city} is estimated at {price_str} "
        f"(~₹{per_sqft:,.0f}/sqft). With {req.amenities_score:.1f}/10 amenities and "
        f"{req.age_years} year(s) of age, it sits in line with comparable {req.furnishing.lower()} "
        f"properties in the area. Buyers should independently verify recent local transactions "
        f"and factor in maintenance costs before deciding. (Template insight — set OPENAI_API_KEY "
        f"for AI-generated analysis.)"
    )


def generate_insight(req: InsightRequest) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _template_insight(req), "template"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        user_prompt = (
            f"Property: {req.bedrooms}BHK, {req.bathrooms} bath, {req.area_sqft} sqft, "
            f"{req.locality}, {req.city}. Age: {req.age_years} years. Furnishing: {req.furnishing}. "
            f"Parking: {req.parking}. Amenities score: {req.amenities_score}/10. "
            f"Model-predicted price: {_format_price(req.predicted_price)}."
        )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=220,
            temperature=0.6,
        )
        text = response.choices[0].message.content.strip()
        return text, "llm"
    except Exception:
        return _template_insight(req), "template"
