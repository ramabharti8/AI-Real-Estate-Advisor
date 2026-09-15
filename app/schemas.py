from typing import Literal

from pydantic import BaseModel, Field

City = Literal["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Chennai", "Ahmedabad"]
Furnishing = Literal["Unfurnished", "Semi-Furnished", "Fully-Furnished"]


class PredictRequest(BaseModel):
    area_sqft: float = Field(..., gt=100, le=20000, description="Built-up area in square feet")
    city: City
    locality: str = Field(..., min_length=1, max_length=100)
    bedrooms: int = Field(..., ge=0, le=10)
    bathrooms: int = Field(..., ge=0, le=10)
    age_years: int = Field(..., ge=0, le=100)
    furnishing: Furnishing
    parking: int = Field(..., ge=0, le=5)
    amenities_score: float = Field(..., ge=0, le=10)


class PredictResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    predicted_price: float
    predicted_price_formatted: str
    currency: str = "INR"
    model_name: str


class InsightRequest(PredictRequest):
    predicted_price: float


class InsightResponse(BaseModel):
    insight: str
    source: Literal["llm", "template"]


class DocumentInfo(BaseModel):
    filename: str
    chunk_count: int
    source_type: Literal["sample", "uploaded"]


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class DocumentUploadResponse(BaseModel):
    filename: str
    chunk_count: int
    source_type: Literal["sample", "uploaded"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class DocumentChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


class DocumentChatResponse(BaseModel):
    answer: str
    sources: list[str]
    source_type: Literal["llm", "template"]


class CityMarketSummary(BaseModel):
    city: str
    listings: int
    median_price: float
    median_price_per_sqft: float
    top_locality: str


class MarketSummaryResponse(BaseModel):
    listings: int
    median_price: float
    median_area_sqft: float
    cities_covered: int
    avg_price_by_city: dict[str, float]
    price_by_furnishing: dict[str, list[float]]
