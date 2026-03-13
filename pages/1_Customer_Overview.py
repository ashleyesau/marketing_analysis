import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import (
    load_css, render_navbar, render_active_filters, get_df,
    fmt_currency, fmt_pct, apply_theme, hbar_theme,
    BLUE_PALETTE, CATEGORICAL_PALETTE, SINGLE_BLUE, SINGLE_TEAL,
    COUNTRY_NAMES, map_countries
)

st.set_page_config(page_title="Customer Overview", layout="wide")
load_css()
render_navbar("pages/1_Customer_Overview")

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data
def load_customers():
    return map_countries(get_df("SELECT * FROM dev.fct_customer_metrics"))

@st.cache_data
def load_cohort():
    return get_df("SELECT * FROM dev.fct_cohort_retention")

df_all    = load_customers()
df_cohort = load_cohort()

# ── Sidebar Filters ───────────────────────────────────────────────────────────

if st.session_state.get("_reset_customer_filters"):
    st.session_state["_reset_customer_filters"] = False
    st.session_state["co_loyalty"] = []
    st.session_state["co_country"] = []
    st.session_state["co_gender"]  = []

loyalty_options = sorted(df_all["loyalty_tier"].dropna().unique().tolist())
country_options = sorted(df_all["country"].dropna().unique().tolist())
gender_options  = sorted(df_all["gender"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("**Filters**")
    sel_loyalty = st.multiselect("Loyalty Tier", loyalty_options, default=[], placeholder="All tiers",     key="co_loyalty")
    sel_country = st.multiselect("Country",       country_options, default=[], placeholder="All countries", key="co_country")
    sel_gender  = st.multiselect("Gender",        gender_options,  default=[], placeholder="All genders",   key="co_gender")

    if st.button("Clear Filters", use_container_width=True):
        st.session_state["_reset_customer_filters"] = True
        st.rerun()

    st.divider()
    st.caption("Source: dev.fct_customer_metrics")

# ── Apply Filters ─────────────────────────────────────────────────────────────

df = df_all.copy()
if sel_loyalty: df = df[df["loyalty_tier"].isin(sel_loyalty)]
if sel_country: df = df[df["country"].isin(sel_country)]
if sel_gender:  df = df[df["gender"].isin(sel_gender)]

# ── Header ────────────────────────────────────────────────────────────────────

st.header("Customer Overview", divider="gray")
st.caption(
    "Customer-level breakdown of LTV segments, loyalty tiers, acquisition channels, "
    "and cohort retention. Filters apply to all charts except the cohort heatmap."
)

active = {}
if sel_loyalty: active["Loyalty Tier"] = ", ".join(sel_loyalty)
if sel_country: active["Country"]      = ", ".join(sel_country)
if sel_gender:  active["Gender"]       = ", ".join(sel_gender)
render_active_filters(active)

# ── KPIs ──────────────────────────────────────────────────────────────────────

total_customers  = len(df)
total_purchasers = int(df["has_purchased"].sum())
pct_converted    = total_purchasers / total_customers * 100 if total_customers else 0
avg_ltv          = df[df["total_revenue"] > 0]["total_revenue"].mean()
avg_orders       = df[df["total_orders"]  > 0]["total_orders"].mean()
total_revenue    = df["total_revenue"].sum()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Customers",  f"{total_customers:,}",      help="Total customers matching the current filter selection.")
k2.metric("Total Purchasers", f"{total_purchasers:,}",     help="Customers with at least one valid purchase.")
k3.metric("Conversion Rate",  fmt_pct(pct_converted),      help="Percentage of filtered customers who have purchased.")
k4.metric("Avg LTV",          fmt_currency(avg_ltv),       help="Average total revenue per purchasing customer in the filtered set.")
k5.metric("Avg Orders",       f"{avg_orders:.1f}",         help="Average number of orders per purchasing customer.")
k6.metric("Total Revenue",    fmt_currency(total_revenue), help="Sum of gross revenue across all filtered customers.")

st.divider()

# ── Row 1: LTV Segments + Loyalty Pyramid ────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    st.subheader("LTV Segments")
    st.caption("High = $1,000+  ·  Mid = $300–999  ·  Low = $1–299  ·  None = never purchased.")
    ltv_order = ["High", "Mid", "Low", "None"]
    ltv = df.groupby("ltv_segment").size().reset_index(name="customers")
    ltv["ltv_segment"] = ltv["ltv_segment"].str.capitalize()
    ltv["ltv_segment"] = pd.Categorical(ltv["ltv_segment"], categories=ltv_order, ordered=True)
    ltv = ltv.sort_values("ltv_segment")

    fig_ltv = go.Figure(go.Bar(
        x=ltv["ltv_segment"],
        y=ltv["customers"],
        marker_color=BLUE_PALETTE[:4],
        marker_line_width=0,
        text=ltv["customers"].apply(lambda v: f"{v:,}"),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{x}</b><br>Customers: %{y:,}<extra></extra>"
    ))
    apply_theme(fig_ltv)
    fig_ltv.update_layout(xaxis_title="LTV Segment", yaxis_title="Customers")
    st.plotly_chart(fig_ltv, use_container_width=True)

with col2:
    st.subheader("Loyalty Tier Distribution")
    st.caption("Bronze is the largest segment (~60%). Platinum is the most exclusive (~3%).")
    loyalty_order  = ["platinum", "gold", "silver", "bronze"]
    loyalty_colors = {"platinum": "#1e3a8a", "gold": "#2563eb", "silver": "#60a5fa", "bronze": "#bfdbfe"}
    loyalty = df.groupby("loyalty_tier").size().reset_index(name="customers")
    loyalty["loyalty_tier"] = pd.Categorical(loyalty["loyalty_tier"], categories=loyalty_order, ordered=True)
    loyalty = loyalty.sort_values("loyalty_tier")

    fig_loyalty = go.Figure(go.Bar(
        x=loyalty["customers"],
        y=loyalty["loyalty_tier"],
        orientation="h",
        marker_color=[loyalty_colors.get(t, SINGLE_BLUE) for t in loyalty["loyalty_tier"]],
        marker_line_width=0,
        text=loyalty["customers"].apply(lambda v: f"{v:,}"),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Customers: %{x:,}<extra></extra>"
    ))
    hbar_theme(fig_loyalty)
    fig_loyalty.update_layout(xaxis_title="Customers", yaxis_title="")
    st.plotly_chart(fig_loyalty, use_container_width=True)

st.divider()

# ── Row 2: Acquisition Channel Mix + Revenue by Acquisition Channel ───────────

col3, col4 = st.columns(2)

with col3:
    st.subheader("Acquisition Channel Mix")
    st.caption("Organic and paid search together account for ~60% of all customers.")
    acq = df.groupby("acquisition_channel").size().reset_index(name="customers")

    fig_acq = go.Figure(go.Pie(
        labels=acq["acquisition_channel"],
        values=acq["customers"],
        hole=0.45,
        marker_colors=BLUE_PALETTE,
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<br>%{percent}<extra></extra>"
    ))
    apply_theme(fig_acq, height=380)
    fig_acq.update_layout(
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
    )
    st.plotly_chart(fig_acq, use_container_width=True)

with col4:
    st.subheader("Revenue by Acquisition Channel")
    st.caption("Total gross revenue attributed to each acquisition channel.")
    rev_acq = (
        df.groupby("acquisition_channel")["total_revenue"]
        .sum()
        .reset_index()
        .sort_values("total_revenue", ascending=True)
    )

    fig_rev = go.Figure(go.Bar(
        x=rev_acq["total_revenue"],
        y=rev_acq["acquisition_channel"],
        orientation="h",
        marker_color=SINGLE_BLUE,
        marker_line_width=0,
        text=rev_acq["total_revenue"].apply(lambda v: fmt_currency(v)),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>"
    ))
    hbar_theme(fig_rev, height=380)
    fig_rev.update_layout(xaxis_title="Total Revenue ($)", yaxis_title="")
    st.plotly_chart(fig_rev, use_container_width=True)

st.divider()

# ── Cohort Retention Heatmap ──────────────────────────────────────────────────

st.subheader("Cohort Retention Heatmap — Revenue by Cohort Month")
st.caption(
    "Each row is a signup cohort month. Each column is months since signup. "
    "Cell values show total revenue generated by that cohort in that month. "
    "Darker = higher revenue. Filters above do not apply to this chart."
)

df_cohort["cohort_month"] = df_cohort["cohort_month"].astype(str).str[:7]
df_cohort["order_month"]  = df_cohort["order_month"].astype(str).str[:7]

pivot = df_cohort.pivot_table(
    index="cohort_month",
    columns="months_since_signup",
    values="total_revenue",
    aggfunc="sum"
).fillna(0)

fig_heatmap = go.Figure(go.Heatmap(
    z=pivot.values,
    x=[f"M{c}" for c in pivot.columns],
    y=pivot.index.tolist(),
    colorscale=[
        [0.0, "#eff6ff"],
        [0.3, "#93c5fd"],
        [0.6, "#2563eb"],
        [1.0, "#1e3a8a"]
    ],
    text=[[fmt_currency(v) for v in row] for row in pivot.values],
    texttemplate="%{text}",
    textfont={"size": 9, "color": "#1e293b"},
    hoverongaps=False,
    hovertemplate="Cohort: %{y}<br>%{x}<br>Revenue: $%{z:,.0f}<extra></extra>"
))
fig_heatmap.update_layout(
    height=620,
    xaxis_title="Months Since Signup",
    yaxis_title="Cohort Month",
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Inter, system-ui, sans-serif", size=12, color="#1e293b"),
    margin=dict(l=16, r=24, t=32, b=16),
)
st.plotly_chart(fig_heatmap, use_container_width=True)
