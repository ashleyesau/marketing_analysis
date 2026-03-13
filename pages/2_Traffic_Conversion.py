import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import (
    load_css, render_navbar, render_active_filters, get_df,
    fmt_pct, apply_theme, hbar_theme,
    BLUE_PALETTE, CATEGORICAL_PALETTE, SINGLE_BLUE, SINGLE_TEAL
)

st.set_page_config(page_title="Traffic & Conversion", layout="wide")
load_css()
render_navbar("pages/2_Traffic_Conversion")

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data
def load_conversion():
    return get_df("SELECT * FROM dev.fct_traffic_conversion")

@st.cache_data
def load_monthly():
    return get_df("SELECT * FROM dev.fct_traffic_monthly")

df_conv    = load_conversion()
df_monthly = load_monthly()

# ── Sidebar Filters ───────────────────────────────────────────────────────────

if st.session_state.get("_reset_traffic_filters"):
    st.session_state["_reset_traffic_filters"] = False
    st.session_state["tc_source"] = []

source_options = sorted(df_conv["traffic_source"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("**Filters**")
    sel_source = st.multiselect("Traffic Source", source_options, default=[], placeholder="All sources", key="tc_source")

    if st.button("Clear Filters", use_container_width=True):
        st.session_state["_reset_traffic_filters"] = True
        st.rerun()

    st.divider()
    st.caption("Source: dev.fct_traffic_conversion, dev.fct_traffic_monthly, dev.fct_experiment_groups")

# ── Apply Filters ─────────────────────────────────────────────────────────────

df_c = df_conv.copy()
df_m = df_monthly.copy()
if sel_source:
    df_c = df_c[df_c["traffic_source"].isin(sel_source)]
    df_m = df_m[df_m["traffic_source"].isin(sel_source)]

# ── Header ────────────────────────────────────────────────────────────────────

st.header("Traffic & Conversion", divider="gray")
st.caption(
    "Conversion rates, bounce rates, and event volume by traffic source. "
    "Based on 2M events from stg_events. Filters apply to all charts."
)

active = {}
if sel_source: active["Traffic Source"] = ", ".join(sel_source)
render_active_filters(active)

# ── KPIs ──────────────────────────────────────────────────────────────────────

total_events     = int(df_c["event_count"].sum())
total_customers  = get_df("SELECT COUNT(DISTINCT customer_id) FROM dev.stg_events").iloc[0, 0]

purchases        = df_c[df_c["event_type"] == "purchase"]["event_count"].sum()
bounces          = df_c[df_c["event_type"] == "bounce"]["event_count"].sum()
total_non_bounce = df_c[df_c["event_type"] != "bounce"]["event_count"].sum()

overall_conversion = purchases / total_non_bounce * 100 if total_non_bounce else 0
overall_bounce     = bounces / total_events * 100 if total_events else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Events",       f"{total_events:,}",              help="Total events across all traffic sources in the filtered selection.")
k2.metric("Unique Customers",   f"{total_customers:,}",           help="Unique customers who generated at least one event.")
k3.metric("Purchase Rate",      fmt_pct(overall_conversion),      help="Purchases as a percentage of all non-bounce events.")
k4.metric("Bounce Rate",        fmt_pct(overall_bounce),          help="Bounce events as a percentage of all events.")

st.divider()

# ── Row 1: Purchase Rate by Source + Bounce Rate by Source ───────────────────

col1, col2 = st.columns(2)

with col1:
    st.subheader("Purchase Rate by Traffic Source")
    st.caption("Email and paid search drive the highest purchase conversion rates.")

    purchases_by_source = df_c[df_c["event_type"] == "purchase"][["traffic_source", "event_count"]].copy()
    totals_by_source    = df_c[df_c["event_type"] != "bounce"].groupby("traffic_source")["event_count"].sum().reset_index(name="total")
    purchase_rate       = purchases_by_source.merge(totals_by_source, on="traffic_source")
    purchase_rate["rate"] = purchase_rate["event_count"] / purchase_rate["total"] * 100
    purchase_rate = purchase_rate.sort_values("rate", ascending=True)

    fig_pr = go.Figure(go.Bar(
        x=purchase_rate["rate"],
        y=purchase_rate["traffic_source"],
        orientation="h",
        marker_color=SINGLE_BLUE,
        marker_line_width=0,
        text=purchase_rate["rate"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Purchase Rate: %{x:.2f}%<extra></extra>"
    ))
    hbar_theme(fig_pr)
    fig_pr.update_layout(xaxis_title="Purchase Rate (%)", yaxis_title="")
    st.plotly_chart(fig_pr, use_container_width=True)

with col2:
    st.subheader("Bounce Rate by Traffic Source")
    st.caption("Bounce rate as a percentage of all events per traffic source.")

    bounces_by_source = df_c[df_c["event_type"] == "bounce"][["traffic_source", "event_count"]].copy()
    totals_all        = df_c.groupby("traffic_source")["event_count"].sum().reset_index(name="total")
    bounce_rate       = bounces_by_source.merge(totals_all, on="traffic_source")
    bounce_rate["rate"] = bounce_rate["event_count"] / bounce_rate["total"] * 100
    bounce_rate = bounce_rate.sort_values("rate", ascending=True)

    fig_br = go.Figure(go.Bar(
        x=bounce_rate["rate"],
        y=bounce_rate["traffic_source"],
        orientation="h",
        marker_color=SINGLE_TEAL,
        marker_line_width=0,
        text=bounce_rate["rate"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{y}</b><br>Bounce Rate: %{x:.2f}%<extra></extra>"
    ))
    hbar_theme(fig_br)
    fig_br.update_layout(xaxis_title="Bounce Rate (%)", yaxis_title="")
    st.plotly_chart(fig_br, use_container_width=True)

st.divider()

# ── Row 2: Event Mix by Source ────────────────────────────────────────────────

st.subheader("Event Mix by Traffic Source")
st.caption("Breakdown of event types per traffic source  -  shows funnel shape across channels.")

event_mix = df_c.pivot_table(
    index="traffic_source",
    columns="event_type",
    values="event_count",
    aggfunc="sum"
).fillna(0).reset_index()

event_types = [c for c in event_mix.columns if c != "traffic_source"]
colors      = CATEGORICAL_PALETTE[:len(event_types)]

fig_mix = go.Figure()
for i, etype in enumerate(event_types):
    fig_mix.add_trace(go.Bar(
        name=etype,
        x=event_mix["traffic_source"],
        y=event_mix[etype],
        marker_color=colors[i],
        marker_line_width=0,
        hovertemplate=f"<b>%{{x}}</b><br>{etype}: %{{y:,}}<extra></extra>"
    ))

fig_mix.update_layout(barmode="stack")
apply_theme(fig_mix)
fig_mix.update_layout(
    xaxis_title="Traffic Source",
    yaxis_title="Event Count",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
)
st.plotly_chart(fig_mix, use_container_width=True)

st.divider()

# ── Row 3: Event Volume Over Time ─────────────────────────────────────────────

st.subheader("Event Volume Over Time by Traffic Source")
st.caption("Monthly event counts per traffic source  -  identifies seasonal and channel trends.")

df_m["event_month"] = pd.to_datetime(df_m["event_month"]).dt.to_period("M").astype(str)
monthly_totals = df_m.groupby(["event_month", "traffic_source"])["event_count"].sum().reset_index()
sources        = monthly_totals["traffic_source"].unique()

fig_trend = go.Figure()
for i, source in enumerate(sources):
    src_df = monthly_totals[monthly_totals["traffic_source"] == source].sort_values("event_month")
    fig_trend.add_trace(go.Scatter(
        x=src_df["event_month"],
        y=src_df["event_count"],
        name=source,
        mode="lines",
        line=dict(color=CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)], width=2),
        hovertemplate=f"<b>{source}</b><br>Month: %{{x}}<br>Events: %{{y:,}}<extra></extra>"
    ))

apply_theme(fig_trend, height=400)
fig_trend.update_layout(
    xaxis_title="Month",
    yaxis_title="Event Count",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Experiment Group Analysis ─────────────────────────────────────────────────

@st.cache_data
def load_experiment():
    return get_df("SELECT * FROM dev.fct_experiment_groups ORDER BY experiment_group")

df_exp = load_experiment()

st.divider()
st.subheader("A/B Test: Experiment Group Performance")
st.caption(
    "Users were randomly assigned to control, variant_a, or variant_b. "
    "Purchase rate = purchases / views. Variant B shows a 36% lift over control."
)

# KPIs
ctrl        = df_exp[df_exp["experiment_group"] == "control"].iloc[0]
var_a       = df_exp[df_exp["experiment_group"] == "variant_a"].iloc[0]
var_b       = df_exp[df_exp["experiment_group"] == "variant_b"].iloc[0]
ctrl_rate   = float(ctrl["purchase_rate"])
var_a_rate  = float(var_a["purchase_rate"])
var_b_rate  = float(var_b["purchase_rate"])

e1, e2, e3 = st.columns(3)
e1.metric("Control Purchase Rate",   f"{ctrl_rate:.1f}%",  help="Baseline purchase rate for the control group.")
e2.metric("Variant A Purchase Rate", f"{var_a_rate:.1f}%", delta=f"{var_a_rate - ctrl_rate:+.1f}pp vs control", help="Purchase rate for variant A.")
e3.metric("Variant B Purchase Rate", f"{var_b_rate:.1f}%", delta=f"{var_b_rate - ctrl_rate:+.1f}pp vs control", help="Purchase rate for variant B.")

st.write("")
col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.markdown("**Purchase Rate by Experiment Group**")

    fig_exp_pr = go.Figure(go.Bar(
        x=df_exp["experiment_group"],
        y=df_exp["purchase_rate"],
        marker_color=BLUE_PALETTE[:3],
        marker_line_width=0,
        text=df_exp["purchase_rate"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        textfont=dict(size=12, color="#475569"),
        hovertemplate="<b>%{x}</b><br>Purchase Rate: %{y:.2f}%<extra></extra>"
    ))
    apply_theme(fig_exp_pr)
    fig_exp_pr.update_layout(xaxis_title="Experiment Group", yaxis_title="Purchase Rate (%)")
    st.plotly_chart(fig_exp_pr, use_container_width=True)

with col_exp2:
    st.markdown("**Funnel Step Rates by Experiment Group**")

    metrics    = ["click_rate", "add_to_cart_rate", "purchase_rate", "bounce_rate"]
    labels     = ["Click Rate", "Add to Cart Rate", "Purchase Rate", "Bounce Rate"]
    groups     = df_exp["experiment_group"].tolist()
    group_colors = CATEGORICAL_PALETTE[:len(groups)]

    fig_funnel = go.Figure()
    for i, row in df_exp.iterrows():
        fig_funnel.add_trace(go.Bar(
            name=row["experiment_group"],
            x=labels,
            y=[float(row[m]) for m in metrics],
            marker_color=group_colors[i % len(group_colors)],
            marker_line_width=0,
            text=[f"{float(row[m]):.1f}%" for m in metrics],
            textposition="outside",
            textfont=dict(size=11, color="#475569"),
            hovertemplate="<b>" + row["experiment_group"] + "</b><br>%{x}: %{y:.2f}%<extra></extra>"
        ))

    fig_funnel.update_layout(barmode="group")
    apply_theme(fig_funnel)
    fig_funnel.update_layout(
        xaxis_title="Funnel Step",
        yaxis_title="Rate (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)
