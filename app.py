import streamlit as st
from utils import (
    load_css, render_navbar, get_df,
    fmt_currency, fmt_pct
)

st.set_page_config(page_title="Marketing Analytics", layout="wide")
load_css()
render_navbar("app")

@st.cache_data
def load_kpis():
    return get_df("""
        SELECT
            COUNT(DISTINCT customer_id)                                              AS total_customers,
            SUM(CASE WHEN has_purchased = 1 THEN 1 ELSE 0 END)                      AS total_purchasers,
            ROUND(
                SUM(CASE WHEN has_purchased = 1 THEN 1 ELSE 0 END) * 100.0
                / COUNT(DISTINCT customer_id), 1
            )                                                                        AS pct_converted,
            ROUND(AVG(CASE WHEN total_revenue > 0 THEN total_revenue END), 2)        AS avg_ltv,
            ROUND(AVG(CASE WHEN total_orders  > 0 THEN total_orders  END), 1)        AS avg_orders,
            SUM(total_revenue)                                                       AS total_revenue
        FROM dev.dim_customers
    """)

df  = load_kpis()
row = df.iloc[0]

# ── Nav card button styles ────────────────────────────────────────────────────

st.markdown("""
<style>
div[data-testid="stButton"].nav-card > button {
    width: 100%;
    height: 100%;
    min-height: 120px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: left;
    white-space: normal;
    color: #1e293b;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.6;
    transition: box-shadow 0.2s, border-color 0.2s;
}
div[data-testid="stButton"].nav-card > button:hover {
    box-shadow: 0 4px 16px rgba(37,99,235,0.12);
    border-color: #93c5fd;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────

st.markdown("""
<div style="
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
    border-radius: 16px;
    padding: 3rem 3rem 2.5rem 3rem;
    margin-bottom: 2rem;
">
    <div style="font-size: 0.85rem; font-weight: 700; color: #93c5fd; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.75rem;">
        Portfolio Project
    </div>
    <div style="font-size: 2.6rem; font-weight: 800; color: white; margin-bottom: 0.75rem; line-height: 1.15;">
        Marketing Analytics Dashboard
    </div>
    <div style="font-size: 1.05rem; color: #bfdbfe; max-width: 680px; line-height: 1.7; margin-bottom: 1.75rem;">
        End-to-end analytics engineering project modelling customer segmentation,
        traffic conversion, product performance, and cohort retention on a synthetic
        e-commerce dataset.
    </div>
    <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
        <span style="background: rgba(255,255,255,0.15); color: white; font-size: 0.85rem; font-weight: 600; padding: 0.35rem 0.9rem; border-radius: 999px;">dbt Core</span>
        <span style="background: rgba(255,255,255,0.15); color: white; font-size: 0.85rem; font-weight: 600; padding: 0.35rem 0.9rem; border-radius: 999px;">DuckDB</span>
        <span style="background: rgba(255,255,255,0.15); color: white; font-size: 0.85rem; font-weight: 600; padding: 0.35rem 0.9rem; border-radius: 999px;">Streamlit</span>
        <span style="background: rgba(255,255,255,0.15); color: white; font-size: 0.85rem; font-weight: 600; padding: 0.35rem 0.9rem; border-radius: 999px;">Jan 2021 – Dec 2023</span>
        <span style="background: rgba(255,255,255,0.15); color: white; font-size: 0.85rem; font-weight: 600; padding: 0.35rem 0.9rem; border-radius: 999px;">100k Customers · 2M Events</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Metric Cards ──────────────────────────────────────────────────────────

st.markdown("#### Snapshot")

kpis = [
    ("Total Customers",  f"{int(row.total_customers):,}", "All distinct customers in the dataset"),
    ("Total Purchasers", f"{int(row.total_purchasers):,}", "Customers with at least one valid purchase"),
    ("Conversion Rate",  fmt_pct(row.pct_converted),      "Percentage of all customers who have purchased"),
    ("Avg Customer LTV", fmt_currency(row.avg_ltv),       "Average gross revenue per purchasing customer"),
    ("Avg Orders",       f"{row.avg_orders:.1f}",         "Average number of orders per purchasing customer"),
    ("Total Revenue",    fmt_currency(row.total_revenue), "Sum of gross revenue across all valid transactions"),
]

cards_html = '<div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 1rem; margin-bottom: 2rem;">'
for label, value, tooltip in kpis:
    cards_html += f"""
    <div title="{tooltip}" style="
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
    ">
        <div style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem;">
            {label}
        </div>
        <div style="font-size: 1.75rem; font-weight: 800; color: #1e293b; line-height: 1.1;">
            {value}
        </div>
    </div>"""
cards_html += '</div>'

st.markdown(cards_html, unsafe_allow_html=True)

st.divider()

# ── Nav Cards ─────────────────────────────────────────────────────────────────

st.markdown("#### Explore")

nav_items = [
    ("Customer Overview",    "LTV segments, loyalty tiers, acquisition channels, and cohort retention heatmap.", "pages/1_Customer_Overview.py"),
    ("Traffic & Conversion", "Purchase and bounce rates by traffic source, event mix, and monthly volume trends.", "pages/2_Traffic_Conversion.py"),
    ("Product Performance",  "Category conversion rates, revenue by product, and discount impact analysis.", "pages/3_Product_Performance.py"),
    ("Campaigns",            "Campaign attribution, revenue by channel, and spend-to-revenue efficiency.", "pages/4_Campaigns.py"),
]

cols = st.columns(4)
for col, (title, description, page) in zip(cols, nav_items):
    with col:
        st.markdown(f"""
        <div style="
            border: 1px solid #e2e8f0;
            border-radius: 12px 12px 0 0;
            border-bottom: none;
            padding: 1.5rem 1.5rem 1rem 1.5rem;
            background: white;
        ">
            <div style="font-size: 1.3rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem;">{title}</div>
            <div style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">{description}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open →", key=f"nav_{page}", use_container_width=True):
            st.switch_page(page)

st.divider()
st.caption("Synthetic e-commerce dataset · Built with dbt + DuckDB + Streamlit · Data covers Jan 2021 – Dec 2023")
