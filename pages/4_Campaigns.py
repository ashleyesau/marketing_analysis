import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import (
    load_css, render_navbar, render_active_filters, get_df,
    fmt_currency, fmt_pct, apply_theme, hbar_theme,
    BLUE_PALETTE, CATEGORICAL_PALETTE, SINGLE_BLUE, SINGLE_TEAL, SINGLE_PURPLE
)

st.set_page_config(page_title="Campaigns", layout="wide")
load_css()
render_navbar("pages/4_Campaigns")

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data
def load_campaigns():
    return get_df("SELECT * FROM dev.dim_campaigns")

@st.cache_data
def load_campaign_transactions():
    return get_df("""
        SELECT
            t.campaign_id,
            t.gross_revenue,
            t.is_refunded,
            c.channel,
            c.objective,
            c.target_segment,
            c.expected_uplift
        FROM dev.fct_transactions t
        LEFT JOIN dev.dim_campaigns c ON t.campaign_id = c.campaign_id
        WHERE t.campaign_id IS NOT NULL
          AND t.gross_revenue > 0
    """)

df_campaigns = load_campaigns()
df_ct        = load_campaign_transactions()

# ── Sidebar Filters ───────────────────────────────────────────────────────────

if st.session_state.get("_reset_campaign_filters"):
    st.session_state["_reset_campaign_filters"] = False
    st.session_state["cp_channel"]   = []
    st.session_state["cp_objective"] = []
    st.session_state["cp_segment"]   = []

channel_options   = sorted(df_campaigns["channel"].dropna().unique().tolist())
objective_options = sorted(df_campaigns["objective"].dropna().unique().tolist())
segment_options   = sorted(df_campaigns["target_segment"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("**Filters**")
    sel_channel   = st.multiselect("Channel",        channel_options,   default=[], placeholder="All channels",   key="cp_channel")
    sel_objective = st.multiselect("Objective",      objective_options, default=[], placeholder="All objectives", key="cp_objective")
    sel_segment   = st.multiselect("Target Segment", segment_options,   default=[], placeholder="All segments",   key="cp_segment")

    if st.button("Clear Filters", use_container_width=True):
        st.session_state["_reset_campaign_filters"] = True
        st.rerun()

    st.divider()
    st.caption("Source: dev.dim_campaigns")
    st.caption("Source: dev.fct_transactions")

# ── Apply Filters ─────────────────────────────────────────────────────────────

df_c = df_campaigns.copy()
df_t = df_ct.copy()

if sel_channel:
    df_c = df_c[df_c["channel"].isin(sel_channel)]
    df_t = df_t[df_t["channel"].isin(sel_channel)]
if sel_objective:
    df_c = df_c[df_c["objective"].isin(sel_objective)]
    df_t = df_t[df_t["objective"].isin(sel_objective)]
if sel_segment:
    df_c = df_c[df_c["target_segment"].isin(sel_segment)]
    df_t = df_t[df_t["target_segment"].isin(sel_segment)]

# ── Header ────────────────────────────────────────────────────────────────────

st.header("Campaigns", divider="gray")
st.caption(
    "Revenue attribution, channel performance, and campaign objective breakdown. "
    "Only transactions with a valid campaign_id are included. "
    "campaign_id = 0 (unattributed) is excluded from all calculations."
)

active = {}
if sel_channel:   active["Channel"]        = ", ".join(sel_channel)
if sel_objective: active["Objective"]      = ", ".join(sel_objective)
if sel_segment:   active["Target Segment"] = ", ".join(sel_segment)
render_active_filters(active)

# ── KPIs ──────────────────────────────────────────────────────────────────────

total_campaigns      = int(df_c["campaign_id"].nunique())
total_channels       = int(df_c["channel"].nunique())
total_attributed_rev = df_t["gross_revenue"].sum()
total_transactions   = len(df_t)
avg_expected_uplift  = df_c["expected_uplift"].mean() * 100
refund_rate          = df_t["is_refunded"].mean() * 100 if len(df_t) else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Campaigns",       f"{total_campaigns:,}",           help="Number of distinct campaigns matching the current filter selection.")
k2.metric("Channels",              f"{total_channels:,}",            help="Number of distinct channels in the filtered campaign set.")
k3.metric("Attributed Revenue",    fmt_currency(total_attributed_rev),help="Total gross revenue from transactions linked to a valid campaign_id.")
k4.metric("Attributed Txns",       f"{total_transactions:,}",        help="Number of transactions attributed to a campaign in the filtered set.")
k5.metric("Avg Expected Uplift",   fmt_pct(avg_expected_uplift),     help="Average expected uplift percentage across all filtered campaigns.")
k6.metric("Refund Rate",           fmt_pct(refund_rate),             help="Percentage of attributed transactions that were refunded.")

st.divider()

# ── Row 1: Revenue by Channel + Objective Breakdown ──────────────────────────

col1, col2 = st.columns(2)

with col1:
    st.subheader("Attributed Revenue by Channel")
    st.caption("Total gross revenue from campaign-attributed transactions grouped by channel.")

    rev_channel = (
        df_t.groupby("channel")["gross_revenue"]
        .sum()
        .reset_index()
        .sort_values("gross_revenue", ascending=True)
    )
    fig_channel = go.Figure(go.Bar(
        x=rev_channel["gross_revenue"],
        y=rev_channel["channel"],
        orientation="h",
        marker_color=SINGLE_BLUE,
        marker_line_width=0,
        text=rev_channel["gross_revenue"].apply(lambda v: fmt_currency(v)),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}<extra></extra>"
    ))
    hbar_theme(fig_channel)
    fig_channel.update_layout(xaxis_title="Total Revenue ($)", yaxis_title="")
    st.plotly_chart(fig_channel, use_container_width=True)

with col2:
    st.subheader("Campaign Objective Breakdown")
    st.caption("Share of campaigns by stated objective across the filtered portfolio.")

    obj_count = (
        df_c.groupby("objective")["campaign_id"]
        .nunique()
        .reset_index(name="campaigns")
    )
    fig_obj = go.Figure(go.Pie(
        labels=obj_count["objective"],
        values=obj_count["campaigns"],
        hole=0.45,
        marker_colors=BLUE_PALETTE,
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>Campaigns: %{value}<br>%{percent}<extra></extra>"
    ))
    apply_theme(fig_obj, height=350)
    fig_obj.update_layout(
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
    )
    st.plotly_chart(fig_obj, use_container_width=True)

st.divider()

# ── Row 2: Transactions by Channel + Target Segment Mix ──────────────────────

col3, col4 = st.columns(2)

with col3:
    st.subheader("Attributed Transactions by Channel")
    st.caption("Transaction count per channel. Compare with revenue to spot high-volume, low-value channels.")

    txn_channel = (
        df_t.groupby("channel")["gross_revenue"]
        .count()
        .reset_index(name="transactions")
        .sort_values("transactions", ascending=True)
    )
    fig_txn = go.Figure(go.Bar(
        x=txn_channel["transactions"],
        y=txn_channel["channel"],
        orientation="h",
        marker_color=SINGLE_TEAL,
        marker_line_width=0,
        text=txn_channel["transactions"].apply(lambda v: f"{v:,}"),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Transactions: %{x:,}<extra></extra>"
    ))
    hbar_theme(fig_txn)
    fig_txn.update_layout(xaxis_title="Transactions", yaxis_title="")
    st.plotly_chart(fig_txn, use_container_width=True)

with col4:
    st.subheader("Target Segment Mix")
    st.caption("Share of campaigns by target customer segment.")

    seg_mix = (
        df_c.groupby("target_segment")["campaign_id"]
        .nunique()
        .reset_index(name="campaigns")
    )
    fig_seg = go.Figure(go.Pie(
        labels=seg_mix["target_segment"],
        values=seg_mix["campaigns"],
        hole=0.45,
        marker_colors=CATEGORICAL_PALETTE,
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>Campaigns: %{value}<br>%{percent}<extra></extra>"
    ))
    apply_theme(fig_seg, height=350)
    fig_seg.update_layout(
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
    )
    st.plotly_chart(fig_seg, use_container_width=True)

st.divider()

# ── Scatter: Expected Uplift vs Attributed Revenue ────────────────────────────

st.subheader("Expected Uplift vs Attributed Revenue by Campaign")
st.caption(
    "Each point is a campaign. X axis is the expected uplift set at campaign creation. "
    "Y axis is actual attributed gross revenue. Coloured by channel. "
    "Campaigns above the trend delivered more revenue than their uplift expectation implied."
)

rev_per_campaign = (
    df_t.groupby("campaign_id")["gross_revenue"]
    .sum()
    .reset_index(name="attributed_revenue")
)
df_scatter = df_c.merge(rev_per_campaign, on="campaign_id", how="left").dropna(
    subset=["expected_uplift", "attributed_revenue"]
)

channels = df_scatter["channel"].unique().tolist()

fig_scatter = go.Figure()
for i, channel in enumerate(channels):
    c = df_scatter[df_scatter["channel"] == channel]
    fig_scatter.add_trace(go.Scatter(
        x=c["expected_uplift"] * 100,
        y=c["attributed_revenue"],
        mode="markers",
        name=channel,
        marker=dict(
            color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)],
            size=10,
            opacity=0.7,
            line=dict(width=0)
        ),
        hovertemplate=(
            f"<b>{channel}</b><br>"
            "Campaign: %{customdata[0]}<br>"
            "Objective: %{customdata[1]}<br>"
            "Expected Uplift: %{x:.1f}%<br>"
            "Attributed Revenue: $%{y:,.0f}<extra></extra>"
        ),
        customdata=c[["campaign_id", "objective"]].values
    ))

apply_theme(fig_scatter, height=440)
fig_scatter.update_layout(xaxis_title="Expected Uplift (%)", yaxis_title="Attributed Revenue ($)")
st.plotly_chart(fig_scatter, use_container_width=True)
