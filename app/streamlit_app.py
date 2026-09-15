"""Streamlit UI. Calls the FastAPI backend over HTTP (API_BASE_URL env var),
keeping the UI, model-serving and LLM logic in separate deployable services.
"""
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "housing_data.csv")

CITIES = ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Chennai", "Ahmedabad"]
LOCALITIES = {
    "Mumbai": ["Andheri", "Bandra", "Powai", "Thane", "Borivali"],
    "Delhi": ["Dwarka", "Rohini", "Saket", "Vasant Kunj", "Karol Bagh"],
    "Bangalore": ["Whitefield", "Koramangala", "Indiranagar", "HSR Layout", "Electronic City"],
    "Pune": ["Hinjewadi", "Kothrud", "Wakad", "Viman Nagar", "Baner"],
    "Hyderabad": ["Gachibowli", "Madhapur", "Kondapur", "Kukatpally", "Banjara Hills"],
    "Chennai": ["Adyar", "OMR", "Velachery", "Anna Nagar", "T Nagar"],
    "Ahmedabad": ["Satellite", "Bopal", "Vastrapur", "Maninagar", "SG Highway"],
}

st.set_page_config(page_title="AI Real Estate Advisor", page_icon=None, layout="wide")

CUSTOM_CSS = """
<style>
:root {
    --ink: #1C2027;
    --ink-dim: #5B5F68;
    --accent: #3A6B5C;
    --accent-soft: #EAF3EF;
    --line: #DCD7C9;
    --warn: #B5652D;
    --warn-soft: #FBEDE1;
}
html, body, [class*="css"] { font-family: "Source Sans Pro", "Segoe UI", sans-serif; }
h1, h2, h3 { letter-spacing: -0.01em; }
.app-header {
    display: flex; align-items: baseline; justify-content: space-between;
    border-bottom: 1px solid var(--line); padding-bottom: 14px; margin-bottom: 22px;
}
.app-header .brand { font-size: 24px; font-weight: 700; color: var(--ink); }
.app-header .tagline { font-size: 13px; color: var(--ink-dim); margin-top: 2px; }
.app-header .status {
    font-family: "Courier New", monospace; font-size: 11px; letter-spacing: .06em;
    text-transform: uppercase; color: var(--accent); border: 1px solid var(--accent);
    border-radius: 4px; padding: 3px 9px;
}
.section-label {
    font-family: "Courier New", monospace; font-size: 11px; letter-spacing: .1em;
    text-transform: uppercase; color: var(--ink-dim); margin: 4px 0 2px;
}
.metric-card {
    border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px;
    background: #FFFFFF;
}
.metric-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--ink-dim); }
.metric-card .value { font-family: "Courier New", monospace; font-size: 22px; font-weight: 700; color: var(--accent); margin-top: 2px; }
.result-panel {
    border: 1px solid var(--line); border-radius: 12px; padding: 20px 22px; background: var(--accent-soft);
}
.result-panel .price { font-family: "Courier New", monospace; font-size: 30px; font-weight: 700; color: var(--accent); }
.result-panel .range { font-size: 13px; color: var(--ink-dim); margin-top: 2px; }
.insight-panel {
    border: 1px solid var(--line); border-radius: 12px; padding: 18px 20px; background: #FFFFFF; margin-top: 14px;
}
.badge {
    font-family: "Courier New", monospace; font-size: 10.5px; font-weight: 700; letter-spacing: .05em;
    text-transform: uppercase; padding: 2px 8px; border-radius: 100px; background: var(--line); color: var(--ink-dim);
}
.badge.llm { background: var(--accent-soft); color: var(--accent); }
.badge.template { background: var(--warn-soft); color: var(--warn); }
footer, #MainMenu { visibility: hidden; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    return None


@st.cache_data
def load_metrics():
    path = os.path.join(os.path.dirname(__file__), "model", "metrics.json")
    if os.path.exists(path):
        import json
        with open(path) as f:
            return json.load(f)
    return None


def check_api_health():
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=3)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException:
        return None


data = load_data()
metrics = load_metrics()
health = check_api_health()

if "history" not in st.session_state:
    st.session_state.history = []

# ---- Header ----
status_text = "API Connected" if health and health.get("model_ready") else "API Unreachable"
st.markdown(
    f"""<div class="app-header">
        <div>
            <div class="brand">AI Real Estate Advisor</div>
            <div class="tagline">Machine-learning price valuation and investment analysis for Indian residential property</div>
        </div>
        <div class="status">{status_text}</div>
    </div>""",
    unsafe_allow_html=True,
)

USD_PER_INR = 1 / 83.0
SQFT_PER_SQM = 10.7639

if "currency" not in st.session_state:
    st.session_state.currency = "INR"
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []


def format_currency(value_inr: float) -> str:
    if st.session_state.currency == "USD":
        v = value_inr * USD_PER_INR
        return f"$ {v / 1000:.1f}K" if v < 1_000_000 else f"$ {v / 1_000_000:.2f}M"
    lakh = value_inr / 100000
    return f"Rs {lakh / 100:.2f} Cr" if lakh >= 100 else f"Rs {lakh:.1f} Lakh"


# ---- Sidebar: advanced tools ----
with st.sidebar:
    st.markdown('<div class="section-label">Display currency</div>', unsafe_allow_html=True)
    st.session_state.currency = st.radio(
        "Currency", ["INR", "USD"], horizontal=True, label_visibility="collapsed",
        index=["INR", "USD"].index(st.session_state.currency),
    )
    st.divider()

    st.markdown('<div class="section-label">City snapshot</div>', unsafe_allow_html=True)
    if data is not None:
        snap_city = st.selectbox("Lookup city", CITIES, key="snapshot_city", label_visibility="collapsed")
        snap = data[data["city"] == snap_city]
        col_a, col_b = st.columns(2)
        col_a.metric("Median price", format_currency(snap["price"].median()))
        col_b.metric("Price / sqft", f"Rs {(snap['price'] / snap['area_sqft']).median():,.0f}")
        top_locality = snap.groupby("locality")["price"].mean().idxmax()
        st.caption(f"Highest-priced locality on record: {top_locality}")
    st.divider()

    st.markdown('<div class="section-label">Unit converter</div>', unsafe_allow_html=True)
    conv_sqft = st.number_input("Sqft", min_value=0.0, value=1000.0, step=50.0, label_visibility="visible")
    st.caption(f"{conv_sqft:,.0f} sqft = {conv_sqft / SQFT_PER_SQM:,.1f} sq.m = {conv_sqft / 43560:.3f} acre")
    st.divider()

    if st.session_state.watchlist:
        st.markdown('<div class="section-label">Watchlist</div>', unsafe_allow_html=True)
        for i, item in enumerate(st.session_state.watchlist):
            wc1, wc2 = st.columns([4, 1])
            wc1.caption(f"{item['locality']}, {item['city']} — {format_currency(item['predicted_price'])}")
            if wc2.button("x", key=f"remove_watch_{i}", help="Remove"):
                st.session_state.watchlist.pop(i)
                st.rerun()
        st.divider()

    if st.session_state.history:
        st.markdown('<div class="section-label">Session history</div>', unsafe_allow_html=True)
        st.caption(f"{len(st.session_state.history)} valuation(s) this session")
        hist_df = pd.DataFrame(st.session_state.history)
        st.download_button(
            "Export history (CSV)",
            data=hist_df.to_csv(index=False),
            file_name="valuation_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# ---- Tabs ----
tab_value, tab_market, tab_finance, tab_history = st.tabs(
    ["Valuation", "Market Insights", "Financing", "History"]
)

# ===== TAB 1: VALUATION =====
with tab_value:
    st.markdown('<div class="section-label">Property details</div>', unsafe_allow_html=True)
    with st.form("property_form"):
        col1, col2 = st.columns(2)
        with col1:
            city = st.selectbox("City", CITIES)
            locality = st.selectbox("Locality", LOCALITIES[city])
            area_sqft = st.number_input("Area (sqft)", min_value=200, max_value=15000, value=1200, step=50)
            bedrooms = st.number_input("Bedrooms", min_value=0, max_value=10, value=2)
        with col2:
            bathrooms = st.number_input("Bathrooms", min_value=0, max_value=10, value=2)
            age_years = st.number_input("Age (years)", min_value=0, max_value=100, value=5)
            furnishing = st.selectbox("Furnishing", ["Unfurnished", "Semi-Furnished", "Fully-Furnished"])
            parking = st.number_input("Parking spots", min_value=0, max_value=5, value=1)
        amenities_score = st.slider("Amenities score", 0.0, 10.0, 6.0, 0.1)
        submitted = st.form_submit_button("Run Valuation", use_container_width=True, type="primary")

    st.caption(
        "Trained on a synthetically generated dataset by default -- see the Handbook "
        "(docs/handbook.html) to retrain on a real, downloaded dataset."
    )

    if submitted:
        payload = {
            "area_sqft": area_sqft,
            "city": city,
            "locality": locality,
            "bedrooms": int(bedrooms),
            "bathrooms": int(bathrooms),
            "age_years": int(age_years),
            "furnishing": furnishing,
            "parking": int(parking),
            "amenities_score": amenities_score,
        }
        try:
            with st.spinner("Running valuation model..."):
                pred_resp = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=15)
                pred_resp.raise_for_status()
                pred = pred_resp.json()

            price = pred["predicted_price"]
            price_per_sqft = price / area_sqft
            margin = metrics["test_mae"] if metrics else price * 0.08
            low, high = max(price - margin, 0), price + margin

            st.markdown(
                f"""<div class="result-panel">
                    <div class="price">{format_currency(price)}</div>
                    <div class="range">Estimated range: {format_currency(low)} &ndash; {format_currency(high)}
                        &nbsp;&middot;&nbsp; Rs {price_per_sqft:,.0f} / sqft
                        &nbsp;&middot;&nbsp; Model: {pred['model_name']}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("Save to watchlist", key="save_watch"):
                st.session_state.watchlist.append({
                    "city": city, "locality": locality, "predicted_price": round(price, 2),
                })
                st.rerun()

            with st.spinner("Generating investment insight..."):
                insight_payload = {**payload, "predicted_price": price}
                insight_resp = requests.post(f"{API_BASE_URL}/insights", json=insight_payload, timeout=30)
                insight_resp.raise_for_status()
                insight = insight_resp.json()

            badge_class = "llm" if insight["source"] == "llm" else "template"
            badge_text = "AI Generated" if insight["source"] == "llm" else "Template Fallback"
            st.markdown(
                f"""<div class="insight-panel">
                    <span class="badge {badge_class}">{badge_text}</span>
                    <p style="margin-top:10px;">{insight['insight']}</p>
                </div>""",
                unsafe_allow_html=True,
            )

            st.session_state.history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "city": city, "locality": locality, "area_sqft": area_sqft,
                "bedrooms": bedrooms, "bathrooms": bathrooms, "furnishing": furnishing,
                "predicted_price": round(price, 2),
                "price_per_sqft": round(price_per_sqft, 2),
            })

            if data is not None:
                comp = data[(data["city"] == city) & (data["bedrooms"] == bedrooms)]
                if len(comp) >= 5:
                    st.markdown('<div class="section-label" style="margin-top:24px;">Comparable listings</div>', unsafe_allow_html=True)
                    fig, ax = plt.subplots(figsize=(7, 4))
                    ax.scatter(comp["area_sqft"], comp["price"] / 100000, alpha=0.4, label="Similar listings", color="#8FA89B")
                    ax.scatter([area_sqft], [price / 100000], color="#B5652D", s=140, label="This property", zorder=5)
                    ax.set_xlabel("Area (sqft)")
                    ax.set_ylabel("Price (Rs Lakh)")
                    ax.set_title(f"{bedrooms}BHK comparables in {city}")
                    ax.legend(frameon=False)
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)
                    st.pyplot(fig)
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not reach the API at {API_BASE_URL}: {exc}")

# ===== TAB 2: MARKET INSIGHTS =====
with tab_market:
    if data is None:
        st.warning("Dataset not found. Run `python src/generate_data.py` first.")
    else:
        st.markdown('<div class="section-label">Portfolio overview</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for col, label, value in [
            (c1, "Listings", f"{len(data):,}"),
            (c2, "Median price", f"Rs {data['price'].median() / 100000:.1f} L"),
            (c3, "Median area", f"{data['area_sqft'].median():.0f} sqft"),
            (c4, "Cities covered", f"{data['city'].nunique()}"),
        ]:
            col.markdown(f'<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:24px;">Average price by city</div>', unsafe_allow_html=True)
        city_avg = data.groupby("city")["price"].mean().sort_values(ascending=False) / 100000
        fig1, ax1 = plt.subplots(figsize=(8, 3.5))
        ax1.bar(city_avg.index, city_avg.values, color="#3A6B5C")
        ax1.set_ylabel("Average price (Rs Lakh)")
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        plt.xticks(rotation=20)
        st.pyplot(fig1)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-label">Price vs. area</div>', unsafe_allow_html=True)
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            ax2.scatter(data["area_sqft"], data["price"] / 100000, alpha=0.25, s=12, color="#3A6B5C")
            ax2.set_xlabel("Area (sqft)")
            ax2.set_ylabel("Price (Rs Lakh)")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            st.pyplot(fig2)
        with col_b:
            st.markdown('<div class="section-label">Price by furnishing</div>', unsafe_allow_html=True)
            fig3, ax3 = plt.subplots(figsize=(5, 4))
            grp = [data[data["furnishing"] == f]["price"] / 100000 for f in data["furnishing"].unique()]
            ax3.boxplot(grp, tick_labels=data["furnishing"].unique(), patch_artist=True,
                        boxprops=dict(facecolor="#EAF3EF", color="#3A6B5C"))
            ax3.set_ylabel("Price (Rs Lakh)")
            ax3.spines["top"].set_visible(False)
            ax3.spines["right"].set_visible(False)
            st.pyplot(fig3)

# ===== TAB 3: FINANCING =====
with tab_finance:
    st.markdown('<div class="section-label">Loan / EMI calculator</div>', unsafe_allow_html=True)
    st.caption("Estimate monthly payments for a property using the last valuation, or enter a price manually.")

    default_price = st.session_state.history[-1]["predicted_price"] if st.session_state.history else 8_000_000.0

    col1, col2 = st.columns(2)
    with col1:
        property_price = st.number_input("Property price (Rs)", min_value=100000.0, value=float(default_price), step=100000.0, format="%.0f")
        down_payment_pct = st.slider("Down payment (%)", 5, 90, 20)
        interest_rate = st.slider("Annual interest rate (%)", 5.0, 15.0, 8.5, 0.1)
    with col2:
        tenure_years = st.slider("Loan tenure (years)", 5, 30, 20)
        down_payment = property_price * down_payment_pct / 100
        loan_amount = property_price - down_payment
        st.metric("Down payment", f"Rs {down_payment:,.0f}")
        st.metric("Loan amount", f"Rs {loan_amount:,.0f}")

    monthly_rate = interest_rate / 12 / 100
    n_months = tenure_years * 12
    if monthly_rate > 0 and loan_amount > 0:
        emi = loan_amount * monthly_rate * (1 + monthly_rate) ** n_months / ((1 + monthly_rate) ** n_months - 1)
    else:
        emi = loan_amount / max(n_months, 1)
    total_payment = emi * n_months
    total_interest = total_payment - loan_amount

    st.markdown('<div class="section-label" style="margin-top:20px;">Result</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="label">Monthly EMI</div><div class="value">Rs {emi:,.0f}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="label">Total interest</div><div class="value">Rs {total_interest:,.0f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="label">Total payment</div><div class="value">Rs {total_payment:,.0f}</div></div>', unsafe_allow_html=True)

# ===== TAB 4: HISTORY =====
with tab_history:
    st.markdown('<div class="section-label">Session valuation history</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.caption("No valuations run yet this session. Use the Valuation tab to generate one.")
    else:
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

st.divider()
st.caption("Backend: FastAPI serving a scikit-learn regression pipeline. Insight generation: OpenAI-compatible LLM with a rule-based template fallback.")
