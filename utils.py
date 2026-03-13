import duckdb
import pathlib
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

DB_PATH = str(pathlib.Path(__file__).parent / "marketing.duckdb")

# ── Palette ───────────────────────────────────────────────────────────────────

BLUE_PALETTE = [
    "#1e3a8a", "#1d4ed8", "#2563eb", "#3b82f6",
    "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe"
]

CATEGORICAL_PALETTE = [
    "#2563eb", "#7c3aed", "#0891b2", "#059669",
    "#d97706", "#dc2626", "#9333ea", "#0284c7"
]

SINGLE_BLUE   = "#2563eb"
SINGLE_RED    = "#ef4444"
SINGLE_TEAL   = "#0891b2"
SINGLE_PURPLE = "#7c3aed"

# ── Plotly theme ──────────────────────────────────────────────────────────────

LAYOUT_DEFAULTS = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Inter, system-ui, sans-serif", size=13, color="#1e293b"),
    margin=dict(l=16, r=24, t=32, b=16),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#e2e8f0",
        font_size=13,
        font_family="Inter, system-ui, sans-serif"
    ),
    xaxis=dict(
        showgrid=False,
        showline=True,
        linecolor="#e2e8f0",
        tickfont=dict(size=12, color="#64748b"),
        title_font=dict(size=13, color="#64748b"),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#f1f5f9",
        showline=False,
        tickfont=dict(size=12, color="#64748b"),
        title_font=dict(size=13, color="#64748b"),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#475569"),
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
)

def apply_theme(fig, height=380):
    fig.update_layout(height=height, **LAYOUT_DEFAULTS)
    return fig

def hbar_theme(fig, height=350):
    """Horizontal bar  -  flip grid to x axis."""
    fig.update_layout(height=height, **LAYOUT_DEFAULTS)
    fig.update_xaxes(showgrid=True,  gridcolor="#f1f5f9", showline=False)
    fig.update_yaxes(showgrid=False, showline=True, linecolor="#e2e8f0")
    return fig

# ── Database ──────────────────────────────────────────────────────────────────

def get_df(sql: str):
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute(sql).df()
    con.close()
    return df

# ── CSS ───────────────────────────────────────────────────────────────────────

def load_css():
    st.markdown("""
    <style>

    /* Hide native Streamlit sidebar navigation */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Hide default Streamlit header */
    header[data-testid="stHeader"] { display: none !important; }

    /* ── Active Filter Tags ── */
    .filter-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    .filter-tag {
        background-color: #dbeafe;
        color: #1d4ed8;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
    }
    .filter-tag-none {
        color: #94a3b8;
        font-size: 0.75rem;
        font-style: italic;
    }

    /* ── General layout ── */
    .block-container {
        padding-top: 1rem !important;
    }

    </style>
    """, unsafe_allow_html=True)

# ── Sidebar Nav ───────────────────────────────────────────────────────────────

def render_navbar(current: str):
    with st.sidebar:
        st.markdown("### Marketing Analytics")
        st.divider()
        st.page_link("app.py",                          label="Home")
        st.page_link("pages/1_Customer_Overview.py",    label="Customer Overview")
        st.page_link("pages/2_Traffic_Conversion.py",    label="Traffic & Conversion")
        st.page_link("pages/3_Product_Performance.py",  label="Product Performance")
        st.page_link("pages/4_Campaigns.py",            label="Campaigns")
        st.divider()

# ── Active Filters ────────────────────────────────────────────────────────────

def render_active_filters(filters: dict):
    st.markdown("**Active Filters**")
    if not filters:
        st.markdown(
            '<div class="filter-tags"><span class="filter-tag-none">None  -  showing all data</span></div>',
            unsafe_allow_html=True
        )
    else:
        tags = "".join(
            f'<span class="filter-tag">{k}: {v}</span>'
            for k, v in filters.items()
        )
        st.markdown(f'<div class="filter-tags">{tags}</div>', unsafe_allow_html=True)

# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.2f}"

def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"

def delta_color(value: float) -> str:
    return "normal" if value >= 0 else "inverse"

# ── Country mapping ───────────────────────────────────────────────────────────

COUNTRY_NAMES = {
    "au": "Australia",
    "br": "Brazil",
    "ca": "Canada",
    "de": "Germany",
    "in": "India",
    "uk": "United Kingdom",
    "us": "United States",
}

def map_countries(df, col="country"):
    df = df.copy()
    df[col] = df[col].map(COUNTRY_NAMES).fillna(df[col])
    return df

# ── Home page nav cards ───────────────────────────────────────────────────────

def render_nav_card(icon: str, title: str, description: str, href: str):
    st.markdown(f"""
    <a href="{href}" target="_self" style="text-decoration:none;">
        <div style="
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            background: white;
            transition: box-shadow 0.2s;
            cursor: pointer;
            height: 100%;
        " onmouseover="this.style.boxShadow='0 4px 16px rgba(37,99,235,0.10)'"
           onmouseout="this.style.boxShadow='none'">
            <div style="font-size: 1.6rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.35rem;">{title}</div>
            <div style="font-size: 0.82rem; color: #64748b; line-height: 1.5;">{description}</div>
        </div>
    </a>
    """, unsafe_allow_html=True)
