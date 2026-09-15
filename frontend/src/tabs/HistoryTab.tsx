import type { HistoryEntry } from "../types";

interface Props {
  history: HistoryEntry[];
  onClear: () => void;
}

function toCsv(rows: HistoryEntry[]): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]);
  const lines = [headers.join(",")];
  for (const row of rows) {
    lines.push(headers.map((h) => JSON.stringify((row as never)[h] ?? "")).join(","));
  }
  return lines.join("\n");
}

export default function HistoryTab({ history, onClear }: Props) {
  function exportCsv() {
    const csv = toCsv(history);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "valuation_history.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="section-label">Session valuation history</div>
      {history.length === 0 ? (
        <p className="caption">No valuations run yet this session. Use the Valuation tab to generate one.</p>
      ) : (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginBottom: 12 }}>
            <button className="btn-secondary" onClick={exportCsv}>
              Export CSV
            </button>
            <button className="btn-secondary" onClick={onClear}>
              Clear history
            </button>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>City</th>
                  <th>Locality</th>
                  <th>Area</th>
                  <th>BHK</th>
                  <th>Furnishing</th>
                  <th>Price</th>
                  <th>Rs/sqft</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i}>
                    <td>{h.timestamp}</td>
                    <td>{h.city}</td>
                    <td>{h.locality}</td>
                    <td>{h.area_sqft}</td>
                    <td>{h.bedrooms}</td>
                    <td>{h.furnishing}</td>
                    <td>Rs {(h.predicted_price / 100000).toFixed(1)} L</td>
                    <td>{h.price_per_sqft.toFixed(0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
