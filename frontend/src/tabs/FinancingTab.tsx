import { useMemo, useState } from "react";

interface Props {
  defaultPrice: number;
}

export default function FinancingTab({ defaultPrice }: Props) {
  const [price, setPrice] = useState(defaultPrice || 8_000_000);
  const [downPct, setDownPct] = useState(20);
  const [rate, setRate] = useState(8.5);
  const [years, setYears] = useState(20);

  const { downPayment, loanAmount, emi, totalInterest, totalPayment } = useMemo(() => {
    const downPayment = (price * downPct) / 100;
    const loanAmount = price - downPayment;
    const monthlyRate = rate / 12 / 100;
    const nMonths = years * 12;
    let emi: number;
    if (monthlyRate > 0 && loanAmount > 0) {
      emi =
        (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, nMonths)) /
        (Math.pow(1 + monthlyRate, nMonths) - 1);
    } else {
      emi = loanAmount / Math.max(nMonths, 1);
    }
    const totalPayment = emi * nMonths;
    const totalInterest = totalPayment - loanAmount;
    return { downPayment, loanAmount, emi, totalInterest, totalPayment };
  }, [price, downPct, rate, years]);

  return (
    <div>
      <div className="section-label">Loan / EMI calculator</div>
      <p className="caption">
        Estimate monthly payments for a property using the last valuation, or enter a price manually.
      </p>

      <div className="card">
        <div className="form-grid">
          <div className="field">
            <label>Property price (Rs)</label>
            <input type="number" min={100000} step={100000} value={price} onChange={(e) => setPrice(Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Down payment ({downPct}%)</label>
            <input type="range" min={5} max={90} value={downPct} onChange={(e) => setDownPct(Number(e.target.value))} />
          </div>
          <div className="field">
            <label>Annual interest rate ({rate.toFixed(1)}%)</label>
            <input
              type="range"
              min={5}
              max={15}
              step={0.1}
              value={rate}
              onChange={(e) => setRate(Number(e.target.value))}
            />
          </div>
          <div className="field">
            <label>Loan tenure ({years} years)</label>
            <input type="range" min={5} max={30} value={years} onChange={(e) => setYears(Number(e.target.value))} />
          </div>
        </div>

        <div className="metric-grid" style={{ marginTop: 16 }}>
          <div className="metric-card">
            <div className="label">Down payment</div>
            <div className="value">Rs {downPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          </div>
          <div className="metric-card">
            <div className="label">Loan amount</div>
            <div className="value">Rs {loanAmount.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          </div>
        </div>
      </div>

      <div className="section-label" style={{ marginTop: 20 }}>
        Result
      </div>
      <div className="metric-grid">
        <div className="metric-card">
          <div className="label">Monthly EMI</div>
          <div className="value">Rs {emi.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div className="metric-card">
          <div className="label">Total interest</div>
          <div className="value">Rs {totalInterest.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div className="metric-card">
          <div className="label">Total payment</div>
          <div className="value">Rs {totalPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
      </div>
    </div>
  );
}
