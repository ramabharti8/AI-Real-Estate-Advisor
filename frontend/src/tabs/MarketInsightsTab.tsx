import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api, type MarketSummary } from "../api/client";

export default function MarketInsightsTab() {
  const [data, setData] = useState<MarketSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.marketSummary().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return <p className="error-text">Dataset not found. Run `python src/generate_data.py` first. ({error})</p>;
  }
  if (!data) return <p className="caption">Loading market data...</p>;

  const cityChart = Object.entries(data.avg_price_by_city)
    .sort((a, b) => b[1] - a[1])
    .map(([city, price]) => ({ city, price }));

  const furnishingChart = Object.entries(data.price_by_furnishing).map(([f, values]) => {
    const sorted = [...values].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)] || 0;
    return { furnishing: f, median };
  });

  return (
    <div>
      <div className="section-label">Portfolio overview</div>
      <div className="metric-grid">
        <div className="metric-card">
          <div className="label">Listings</div>
          <div className="value">{data.listings.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <div className="label">Median price</div>
          <div className="value">Rs {(data.median_price / 100000).toFixed(1)} L</div>
        </div>
        <div className="metric-card">
          <div className="label">Median area</div>
          <div className="value">{data.median_area_sqft.toFixed(0)} sqft</div>
        </div>
        <div className="metric-card">
          <div className="label">Cities covered</div>
          <div className="value">{data.cities_covered}</div>
        </div>
      </div>

      <div className="section-label" style={{ marginTop: 24 }}>
        Average price by city (Rs Lakh)
      </div>
      <div className="card">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={cityChart}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis dataKey="city" stroke="var(--ink-dim)" />
            <YAxis stroke="var(--ink-dim)" />
            <Tooltip />
            <Bar dataKey="price" fill="var(--accent)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="section-label" style={{ marginTop: 24 }}>
        Median price by furnishing (Rs Lakh)
      </div>
      <div className="card">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={furnishingChart}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis dataKey="furnishing" stroke="var(--ink-dim)" />
            <YAxis stroke="var(--ink-dim)" />
            <Tooltip />
            <Bar dataKey="median" fill="var(--warn)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
