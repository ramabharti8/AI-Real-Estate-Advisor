import type { City, Furnishing } from "./api/client";

export interface HistoryEntry {
  timestamp: string;
  city: City;
  locality: string;
  area_sqft: number;
  bedrooms: number;
  bathrooms: number;
  furnishing: Furnishing;
  predicted_price: number;
  price_per_sqft: number;
}
