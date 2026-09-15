import { useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  api,
  CITIES,
  LOCALITIES,
  type City,
  type Furnishing,
  type PredictRequest,
} from "../api/client";
import type { HistoryEntry } from "../types";

interface Props {
  currency: "INR" | "USD";
  formatCurrency: (v: number) => string;
  onSaved: (entry: HistoryEntry) => void;
}

const FURNISHINGS: Furnishing[] = ["Unfurnished", "Semi-Furnished", "Fully-Furnished"];

export default function ValuationTab({ formatCurrency, onSaved }: Props) {
  const [form, setForm] = useState<PredictRequest>({
    area_sqft: 1200,
    city: "Pune",
    locality: LOCALITIES.Pune[0],
    bedrooms: 2,
    bathrooms: 2,
    age_years: 5,
    furnishing: "Semi-Furnished",
    parking: 1,
    amenities_score: 6,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    price: number;
    formatted: string;
    modelName: string;
    pricePerSqft: number;
  } | null>(null);
  const [insight, setInsight] = useState<{ text: string; source: "llm" | "template" } | null>(null);

  function update<K extends keyof PredictRequest>(key: K, value: PredictRequest[K]) {
    setForm((f) => {
      const next = { ...f, [key]: value };
      if (key === "city") next.locality = LOCALITIES[value as City][0];
      return next;
    });
  }

  async function runValuation(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setInsight(null);
    try {
      const pred = await api.predict(form);
      const pricePerSqft = pred.predicted_price / form.area_sqft;
      setResult({
        price: pred.predicted_price,
        formatted: pred.predicted_price_formatted,
        modelName: pred.model_name,
        pricePerSqft,
      });

      onSaved({
        timestamp: new Date().toLocaleString(),
        city: form.city,
        locality: form.locality,
        area_sqft: form.area_sqft,
        bedrooms: form.bedrooms,
        bathrooms: form.bathrooms,
        furnishing: form.furnishing,
        predicted_price: pred.predicted_price,
        price_per_sqft: pricePerSqft,
      });

      const ins = await api.insights({ ...form, predicted_price: pred.predicted_price });
      setInsight({ text: ins.insight, source: ins.source });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const margin = result ? result.price * 0.08 : 0;
  const comparableSeed = result
    ? Array.from({ length: 14 }, (_, i) => ({
        area: form.area_sqft * (0.7 + (i / 13) * 0.7),
        priceLakh: (result.price * (0.75 + Math.random() * 0.5)) / 100000,
      }))
    : [];

  return (
    <div>
      <div className="section-label">Property details</div>
      <form className="card" onSubmit={runValuation}>
        <div className="form-grid">
          <div className="field">
            <label>City</label>
            <select value={form.city} onChange={(e) => update("city", e.target.value as City)}>
              {CITIES.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Locality</label>
            <select value={form.locality} onChange={(e) => update("locality", e.target.value)}>
              {LOCALITIES[form.city].map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Area (sqft)</label>
            <input
              type="number"
              min={200}
              max={15000}
              value={form.area_sqft}
              onChange={(e) => update("area_sqft", Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label>Bedrooms</label>
            <input
              type="number"
              min={0}
              max={10}
              value={form.bedrooms}
              onChange={(e) => update("bedrooms", Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label>Bathrooms</label>
            <input
              type="number"
              min={0}
              max={10}
              value={form.bathrooms}
              onChange={(e) => update("bathrooms", Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label>Age (years)</label>
            <input
              type="number"
              min={0}
              max={100}
              value={form.age_years}
              onChange={(e) => update("age_years", Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label>Furnishing</label>
            <select value={form.furnishing} onChange={(e) => update("furnishing", e.target.value as Furnishing)}>
              {FURNISHINGS.map((f) => (
                <option key={f}>{f}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Parking spots</label>
            <input
              type="number"
              min={0}
              max={5}
              value={form.parking}
              onChange={(e) => update("parking", Number(e.target.value))}
            />
          </div>
          <div className="field" style={{ gridColumn: "1 / -1" }}>
            <label>Amenities score ({form.amenities_score.toFixed(1)} / 10)</label>
            <input
              type="range"
              min={0}
              max={10}
              step={0.1}
              value={form.amenities_score}
              onChange={(e) => update("amenities_score", Number(e.target.value))}
            />
          </div>
        </div>
        <div style={{ marginTop: 16 }}>
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Running valuation..." : "Run Valuation"}
          </button>
        </div>
      </form>

      <p className="caption" style={{ marginTop: 10 }}>
        Trained on a synthetically generated dataset by default. See the Handbook (docs/handbook.html) to retrain on
        a real, downloaded dataset.
      </p>

      {error && <p className="error-text" style={{ marginTop: 14 }}>Could not reach the API: {error}</p>}

      {result && (
        <div className="result-panel" style={{ marginTop: 18 }}>
          <div className="price">{formatCurrency(result.price)}</div>
          <div className="range">
            Estimated range: {formatCurrency(Math.max(result.price - margin, 0))} &ndash;{" "}
            {formatCurrency(result.price + margin)} &middot; Rs {result.pricePerSqft.toLocaleString(undefined, {
              maximumFractionDigits: 0,
            })} / sqft &middot; Model: {result.modelName}
          </div>
        </div>
      )}

      {insight && (
        <div className="insight-panel">
          <span className={`badge ${insight.source}`}>
            {insight.source === "llm" ? "AI Generated" : "Template Fallback"}
          </span>
          <p style={{ marginTop: 10 }}>{insight.text}</p>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24 }}>
          <div className="section-label">Comparable listings (simulated around estimate)</div>
          <div className="card">
            <ResponsiveContainer width="100%" height={260}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                <CartesianGrid stroke="var(--line)" />
                <XAxis dataKey="area" name="Area" unit=" sqft" stroke="var(--ink-dim)" />
                <YAxis dataKey="priceLakh" name="Price" unit=" L" stroke="var(--ink-dim)" />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={comparableSeed} fill="var(--ink-dim)" opacity={0.5} />
                <Scatter
                  data={[{ area: form.area_sqft, priceLakh: result.price / 100000 }]}
                  fill="var(--warn)"
                />
              </ScatterChart>
            </ResponsiveContainer>
            <p className="caption">
              This property vs. simulated comparable {form.bedrooms}BHK listings in {form.city} (illustrative
              scatter derived from the estimate; not real listing data).
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
