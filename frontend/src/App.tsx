import { useEffect, useState } from "react";
import { api } from "./api/client";
import type { HistoryEntry } from "./types";
import Sidebar from "./components/Sidebar";
import ValuationTab from "./tabs/ValuationTab";
import MarketInsightsTab from "./tabs/MarketInsightsTab";
import FinancingTab from "./tabs/FinancingTab";
import HistoryTab from "./tabs/HistoryTab";
import DocumentsTab from "./tabs/DocumentsTab";

const TABS = ["Valuation", "Market Insights", "Financing", "History", "Documents"] as const;
type Tab = (typeof TABS)[number];

const USD_PER_INR = 1 / 83.0;
const HISTORY_KEY = "areAdvisor.history";

export default function App() {
  const [tab, setTab] = useState<Tab>("Valuation");
  const [apiUp, setApiUp] = useState<boolean | null>(null);
  const [currency, setCurrency] = useState<"INR" | "USD">("INR");
  const [history, setHistory] = useState<HistoryEntry[]>(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      return raw ? (JSON.parse(raw) as HistoryEntry[]) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    api
      .health()
      .then((h) => setApiUp(!!h.model_ready))
      .catch(() => setApiUp(false));
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    } catch {
      // ignore storage errors (private mode, quota, etc.)
    }
  }, [history]);

  function formatCurrency(valueInr: number): string {
    if (currency === "USD") {
      const v = valueInr * USD_PER_INR;
      return v < 1_000_000 ? `$ ${(v / 1000).toFixed(1)}K` : `$ ${(v / 1_000_000).toFixed(2)}M`;
    }
    const lakh = valueInr / 100000;
    return lakh >= 100 ? `Rs ${(lakh / 100).toFixed(2)} Cr` : `Rs ${lakh.toFixed(1)} Lakh`;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <div className="brand">AI Real Estate Advisor</div>
          <div className="tagline">
            Machine-learning price valuation and investment analysis for Indian residential property
          </div>
        </div>
        <div className={`status-pill ${apiUp ? "" : "down"}`}>
          {apiUp === null ? "Checking API..." : apiUp ? "API Connected" : "API Unreachable"}
        </div>
      </header>

      <div className="layout">
        <main>
          <nav className="tabs">
            {TABS.map((t) => (
              <button key={t} className={`tab-btn ${t === tab ? "active" : ""}`} onClick={() => setTab(t)}>
                {t}
              </button>
            ))}
          </nav>

          {tab === "Valuation" && (
            <ValuationTab
              currency={currency}
              formatCurrency={formatCurrency}
              onSaved={(entry) => setHistory((h) => [...h, entry])}
            />
          )}
          {tab === "Market Insights" && <MarketInsightsTab />}
          {tab === "Financing" && (
            <FinancingTab defaultPrice={history.length ? history[history.length - 1].predicted_price : 8_000_000} />
          )}
          {tab === "History" && <HistoryTab history={history} onClear={() => setHistory([])} />}
          {tab === "Documents" && <DocumentsTab />}
        </main>

        <Sidebar currency={currency} onCurrencyChange={setCurrency} history={history} />
      </div>

      <footer style={{ marginTop: 40, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
        <p className="caption">
          Backend: FastAPI serving a scikit-learn regression pipeline plus a LangChain/ChromaDB document Q&amp;A
          service. Insight generation: OpenAI-compatible LLM with a rule-based template fallback.
        </p>
      </footer>
    </div>
  );
}
