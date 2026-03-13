import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import (
    load_css, render_navbar, render_active_filters, get_df,
    fmt_currency, fmt_pct, apply_theme, hbar_theme,
    BLUE_PALETTE, CATEGORICAL_PALETTE, SINGLE_BLUE, SINGLE_RED, SINGLE_TEAL, SINGLE_PURPLE
)

st.set_page_config(page_title="Product Performance", layout="wide")
load_css()
render_navbar("pages/3_Product_Performance")

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data
def load_products():
    return get_df("SELECT * FROM dev.fct_product_conversion")

df_all = load_products()

# ── Sidebar Filters ───────────────────────────────────────────────────────────

if st.session_state.get("_reset_product_filters"):
    st.session_state["_reset_product_filters"] = False
    st.session_state["pp_category"] = []
    st.session_state["pp_brand"]    = []

category_options = sorted(df_all["category"].dropna().unique().tolist())
brand_options    = sorted(df_all["brand"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("**Filters**")
    sel_category = st.multiselect("Category", category_options, default=[], placeholder="All categories", key="pp_category")
    sel_brand    = st.multiselect("Brand",    brand_options,    default=[], placeholder="All brands",     key="pp_brand")

    if st.button("Clear Filters", use_container_width=True):
        st.session_state["_reset_product_filters"] = True
        st.rerun()

    st.divider()
    st.caption("Source: dev.fct_product_conversion")

# ── Apply Filters ─────────────────────────────────────────────────────────────

df = df_all.copy()
if sel_category: df = df[df["category"].isin(sel_category)]
if sel_brand:    df = df[df["brand"].isin(sel_brand)]

# ── Header ────────────────────────────────────────────────────────────────────

st.header("Product Performance", divider="gray")
st.caption(
    "Revenue, pricing, and transaction breakdown across product categories and brands. "
    "Conversion rate metrics are excluded — synthetic data produces uniform rates with no "
    "meaningful variance across categories. All charts use real transaction data."
)

active = {}
if sel_category: active["Category"] = ", ".join(sel_category)
if sel_brand:    active["Brand"]    = ", ".join(sel_brand)
render_active_filters(active)

# ── KPIs ──────────────────────────────────────────────────────────────────────

total_products     = int(df["product_id"].nunique())
total_revenue      = df["total_revenue"].sum()
total_transactions = int(df["total_transactions"].sum())
total_buyers       = int(df["unique_buyers"].sum())
avg_order_value    = df[df["avg_order_value"] > 0]["avg_order_value"].mean()
total_discount     = df["total_discount"].sum()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Products",      f"{total_products:,}",         help="Distinct products matching the current filter selection.")
k2.metric("Total Revenue",       fmt_currency(total_revenue),   help="Sum of gross revenue across all valid transactions.")
k3.metric("Total Transactions",  f"{total_transactions:,}",     help="Total number of valid purchase transactions.")
k4.metric("Unique Buyers",       f"{total_buyers:,}",           help="Distinct customers who purchased at least one product in the filtered set.")
k5.metric("Avg Order Value",     fmt_currency(avg_order_value), help="Average transaction value across all filtered products.")
k6.metric("Total Discounts",     fmt_currency(total_discount),  help="Total discount value applied across all transactions in the filtered set.")

st.divider()

# ── Row 1: Revenue by Category + Avg Order Value by Category ─────────────────

col1, col2 = st.columns(2)

with col1:
    st.subheader("Total Revenue by Category")
    st.caption("Gross revenue summed across all transactions per product category.")

    cat_rev = (
        df.groupby("category")["total_revenue"]
        .sum()
        .reset_index()
        .sort_values("total_revenue", ascending=True)
    )
    fig_rev = go.Figure(go.Bar(
        x=cat_rev["total_revenue"],
        y=cat_rev["category"],
        orientation="h",
        marker_color=SINGLE_TEAL,
        marker_line_width=0,
        text=cat_rev["total_revenue"].apply(lambda v: fmt_currency(v)),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>"
    ))
    hbar_theme(fig_rev)
    fig_rev.update_layout(xaxis_title="Total Revenue ($)", yaxis_title="")
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    st.subheader("Avg Order Value by Category")
    st.caption("Average transaction value per category — reflects price point differences across segments.")

    cat_aov = (
        df.groupby("category")["avg_order_value"]
        .mean()
        .reset_index()
        .sort_values("avg_order_value", ascending=True)
    )
    fig_aov = go.Figure(go.Bar(
        x=cat_aov["avg_order_value"],
        y=cat_aov["category"],
        orientation="h",
        marker_color=SINGLE_BLUE,
        marker_line_width=0,
        text=cat_aov["avg_order_value"].apply(lambda v: fmt_currency(v)),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Avg Order Value: $%{x:,.2f}<extra></extra>"
    ))
    hbar_theme(fig_aov)
    fig_aov.update_layout(xaxis_title="Avg Order Value ($)", yaxis_title="")
    st.plotly_chart(fig_aov, use_container_width=True)

st.divider()

# ── Row 2: Top 20 Products by Revenue + Discount by Category ─────────────────

col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 20 Products by Revenue")
    st.caption("Highest-revenue products. Identified by product_id — no product name in source data.")

    top20 = (
        df[df["total_revenue"] > 0]
        .sort_values("total_revenue", ascending=False)
        .head(20)
        .sort_values("total_revenue", ascending=True)
    )
    fig_top20 = go.Figure(go.Bar(
        x=top20["total_revenue"],
        y=top20["product_id"].astype(str),
        orientation="h",
        marker_color=SINGLE_PURPLE,
        marker_line_width=0,
        text=top20["total_revenue"].apply(lambda v: fmt_currency(v)),
        textposition="outside",
        textfont=dict(size=11, color="#475569"),
        hovertemplate="<b>Product %{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>"
    ))
    hbar_theme(fig_top20, height=520)
    fig_top20.update_layout(xaxis_title="Total Revenue ($)", yaxis_title="Product ID")
    st.plotly_chart(fig_top20, use_container_width=True)

with col4:
    st.subheader("Total Discount by Category")
    st.caption("Total discount value applied per category — indicates promotional intensity.")

    cat_disc = (
        df.groupby("category")["total_discount"]
        .sum()
        .reset_index()
        .sort_values("total_discount", ascending=True)
    )
    fig_disc = go.Figure(go.Bar(
        x=cat_disc["total_discount"],
        y=cat_disc["category"],
        orientation="h",
        marker_color=SINGLE_RED,
        marker_line_width=0,
        text=cat_disc["total_discount"].apply(lambda v: fmt_currency(v)),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Total Discount: $%{x:,.2f}<extra></extra>"
    ))
    hbar_theme(fig_disc, height=520)
    fig_disc.update_layout(xaxis_title="Total Discount ($)", yaxis_title="")
    st.plotly_chart(fig_disc, use_container_width=True)

st.divider()

# ── Scatter: Revenue vs Base Price ────────────────────────────────────────────

st.subheader("Total Revenue vs Base Price by Product")
st.caption(
    "Each point is a product. X axis is base price, Y axis is total revenue. "
    "Coloured by category. Identifies whether higher-priced products generate "
    "disproportionately more revenue within and across categories."
)

df_scatter = df[df["total_revenue"] > 0].copy()
categories = df_scatter["category"].unique().tolist()

fig_scatter = go.Figure()
for i, cat in enumerate(categories):
    c = df_scatter[df_scatter["category"] == cat]
    fig_scatter.add_trace(go.Scatter(
        x=c["base_price"],
        y=c["total_revenue"],
        mode="markers",
        name=cat,
        marker=dict(
            color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)],
            size=8,
            opacity=0.65,
            line=dict(width=0)
        ),
        hovertemplate=(
            f"<b>{cat}</b><br>"
            "Product ID: %{customdata}<br>"
            "Base Price: $%{x:,.2f}<br>"
            "Total Revenue: $%{y:,.0f}<extra></extra>"
        ),
        customdata=c["product_id"]
    ))

apply_theme(fig_scatter, height=440)
fig_scatter.update_layout(xaxis_title="Base Price ($)", yaxis_title="Total Revenue ($)")
st.plotly_chart(fig_scatter, use_container_width=True)
