export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type City =
  | "Mumbai"
  | "Delhi"
  | "Bangalore"
  | "Pune"
  | "Hyderabad"
  | "Chennai"
  | "Ahmedabad";

export type Furnishing = "Unfurnished" | "Semi-Furnished" | "Fully-Furnished";

export const CITIES: City[] = [
  "Mumbai",
  "Delhi",
  "Bangalore",
  "Pune",
  "Hyderabad",
  "Chennai",
  "Ahmedabad",
];

export const LOCALITIES: Record<City, string[]> = {
  Mumbai: ["Andheri", "Bandra", "Powai", "Thane", "Borivali"],
  Delhi: ["Dwarka", "Rohini", "Saket", "Vasant Kunj", "Karol Bagh"],
  Bangalore: ["Whitefield", "Koramangala", "Indiranagar", "HSR Layout", "Electronic City"],
  Pune: ["Hinjewadi", "Kothrud", "Wakad", "Viman Nagar", "Baner"],
  Hyderabad: ["Gachibowli", "Madhapur", "Kondapur", "Kukatpally", "Banjara Hills"],
  Chennai: ["Adyar", "OMR", "Velachery", "Anna Nagar", "T Nagar"],
  Ahmedabad: ["Satellite", "Bopal", "Vastrapur", "Maninagar", "SG Highway"],
};

export interface PredictRequest {
  area_sqft: number;
  city: City;
  locality: string;
  bedrooms: number;
  bathrooms: number;
  age_years: number;
  furnishing: Furnishing;
  parking: number;
  amenities_score: number;
}

export interface PredictResponse {
  predicted_price: number;
  predicted_price_formatted: string;
  currency: string;
  model_name: string;
}

export interface InsightResponse {
  insight: string;
  source: "llm" | "template";
}

export interface DocumentInfo {
  filename: string;
  chunk_count: number;
  source_type: "sample" | "uploaded";
}

export interface DocumentChatResponse {
  answer: string;
  sources: string[];
  source_type: "llm" | "template";
}

export interface MarketSummary {
  listings: number;
  median_price: number;
  median_area_sqft: number;
  cities_covered: number;
  avg_price_by_city: Record<string, number>;
  price_by_furnishing: Record<string, number[]>;
}

export interface CitySnapshot {
  city: string;
  listings: number;
  median_price: number;
  median_price_per_sqft: number;
  top_locality: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; model_ready: boolean }>("/health"),
  predict: (payload: PredictRequest) =>
    request<PredictResponse>("/predict", { method: "POST", body: JSON.stringify(payload) }),
  insights: (payload: PredictRequest & { predicted_price: number }) =>
    request<InsightResponse>("/insights", { method: "POST", body: JSON.stringify(payload) }),
  marketSummary: () => request<MarketSummary>("/market/summary"),
  marketByCity: (city: string) => request<CitySnapshot>(`/market/by-city/${encodeURIComponent(city)}`),
  listDocuments: () => request<{ documents: DocumentInfo[] }>("/documents"),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ filename: string; chunk_count: number; source_type: string }>("/documents/upload", {
      method: "POST",
      body: form,
    });
  },
  chatDocuments: (question: string, history: { role: string; content: string }[] = []) =>
    request<DocumentChatResponse>("/documents/chat", {
      method: "POST",
      body: JSON.stringify({ question, history }),
    }),
};
