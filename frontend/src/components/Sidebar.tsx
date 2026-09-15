import { useState } from "react";
import { api, CITIES, type City, type CitySnapshot } from "../api/client";
import type { HistoryEntry } from "../types";

interface Props {
  currency: "INR" | "USD";
  onCurrencyChange: (c: "INR" | "USD") => void;
  history: HistoryEntry[];
}

const SQFT_PER_SQM = 10.7639;

export default function Sidebar({ currency, onCurrencyChange, history }: Props) {
  const [snapCity, setSnapCity] = useState<City>("Mumbai");
  const [snapshot, setSnapshot] = useState<CitySnapshot | null>(null);
  const [snapError, setSnapError] = useState<string | null>(null);
  const [sqft, setSqft] = useState(1000);

  async function lookupCity(city: City) {
    setSnapCity(city);
    setSnapError(null);
    try {
      const res = await api.marketByCity(city);
      setSnapshot(res);
    } catch (err) {
      setSnapshot(null);
      setSnapError(err instanceof Error ? err.message : "lookup failed");
    }
  }

  return (
    <aside>
      <div className="sidebar-block">
        <div className="section-label">Display currency</div>
        <div style={{ display: "flex", gap: 8 }}>
          {(["INR", "USD"] as const).map((c) => (
            <button
              key={c}
              className="btn-secondary"
              style={c === currency ? { borderColor: "var(--accent)", color: "var(--accent)" } : undefined}
              onClick={() => onCurrencyChange(c)}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="sidebar-block">
        <div className="section-label">City snapshot</div>
        <select value={snapCity} onChange={(e) => lookupCity(e.target.value as City)} style={{ width: "100%", padding: 8 }}>
          {CITIES.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        {snapError && <p className="caption" style={{ marginTop: 6 }}>{snapError}</p>}
        {snapshot && (
          <div style={{ marginTop: 10 }}>
            <div className="metric-grid">
              <div className="metric-card">
                <div className="label">Median price</div>
                <div className="value">Rs {(snapshot.median_price / 100000).toFixed(1)} L</div>
              </div>
              <div className="metric-card">
                <div className="label">Price / sqft</div>
                <div className="value">Rs {snapshot.median_price_per_sqft.toFixed(0)}</div>
              </div>
            </div>
            <p className="caption" style={{ marginTop: 6 }}>
              Highest-priced locality on record: {snapshot.top_locality}
            </p>
          </div>
        )}
      </div>

      <div className="sidebar-block">
        <div className="section-label">Unit converter</div>
        <input
          type="number"
          min={0}
          step={50}
          value={sqft}
          onChange={(e) => setSqft(Number(e.target.value))}
          style={{ width: "100%", padding: 8, border: "1px solid var(--line)", borderRadius: 6 }}
        />
        <p className="caption" style={{ marginTop: 6 }}>
          {sqft.toLocaleString()} sqft = {(sqft / SQFT_PER_SQM).toLocaleString(undefined, { maximumFractionDigits: 1 })} sq.m
          = {(sqft / 43560).toFixed(3)} acre
        </p>
      </div>

      {history.length > 0 && (
        <div className="sidebar-block">
          <div className="section-label">Session history</div>
          <p className="caption">{history.length} valuation(s) this session</p>
        </div>
      )}
    </aside>
  );
}
