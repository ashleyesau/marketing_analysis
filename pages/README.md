# Streamlit Dashboard

A five-page analytics dashboard reading directly from DuckDB mart tables and surfacing customer, traffic, product, campaign, and A/B experiment insights.

---

## Role in the Wider Project

- Presentation layer of the marketing_analysis stack
- Reads exclusively from mart tables in `marketing.duckdb`; no transformation logic lives in the app
- `utils.py` provides a shared DuckDB connection, Plotly theme, formatting helpers, and sidebar navigation used by every page
- Can be run locally after dbt models are built, or viewed on Streamlit Cloud where it connects to the tracked `marketing.duckdb` file in the repository

---

## What It Contains

- `utils.py` - Shared utilities module: DuckDB connection via `pathlib.Path(__file__).parent` for Streamlit Cloud compatibility; CSS injection; sidebar navigation rendered with `st.page_link()`; shared Plotly theme (LAYOUT_DEFAULTS, apply_theme(), hbar_theme()); colour palettes (BLUE_PALETTE, CATEGORICAL_PALETTE); formatting helpers (fmt_currency(), fmt_pct(), delta_color()); ISO country code to full name mapping for the customer overview page; home page nav card renderer
- `app.py` - Landing page with a gradient hero banner, six KPI summary cards drawn from dim_customers, and an explore section with links to all four analysis pages via st.switch_page()
- `1_Customer_Overview.py` - Customer segmentation page: six KPI cards, LTV segment distribution, loyalty tier breakdown, acquisition channel mix donut, revenue by acquisition channel bar chart, and a cohort retention heatmap pivoted on months_since_signup; sidebar filters for loyalty tier, country, and gender
- `2_Traffic_Conversion.py` - Traffic source conversion page: four KPI cards, purchase rate by source, bounce rate by source, event mix stacked bar, monthly event volume line chart, and an A/B experiment group analysis section with KPI deltas vs control and grouped funnel step rate charts; sidebar filter for traffic source (applies to traffic charts only; experiment section is unfiltered)
- `3_Product_Performance.py` - Product revenue page: six KPI cards, revenue by category, average order value by category, top 20 products by revenue, discount by category, and a revenue vs base price scatter coloured by category; sidebar filters for category and brand
- `4_Campaigns.py` - Campaign attribution page: six KPI cards, revenue by channel, objective breakdown donut, transactions by channel, target segment donut, and an expected uplift vs attributed revenue scatter coloured by channel; sidebar filters for channel, objective, and target segment

---

## Inputs and Outputs

Inputs (all mart tables from `marketing.duckdb`, dev schema):

- `dev.dim_customers` - app.py, 1_Customer_Overview.py
- `dev.fct_customer_metrics` - 1_Customer_Overview.py
- `dev.fct_cohort_retention` - 1_Customer_Overview.py
- `dev.fct_traffic_conversion` - 2_Traffic_Conversion.py
- `dev.fct_traffic_monthly` - 2_Traffic_Conversion.py
- `dev.fct_experiment_groups` - 2_Traffic_Conversion.py
- `dev.fct_product_conversion` - 3_Product_Performance.py
- `dev.dim_campaigns` - 4_Campaigns.py
- `dev.fct_transactions` - 4_Campaigns.py

Outputs:

- Interactive web dashboard rendered in the browser; no files written at runtime

---

## Notes

- All inner pages use `st.metric()` with `help=` tooltips for KPI display. The home page (app.py) uses custom HTML metric cards, which is the only exception to this pattern.
- Sidebar navigation uses `st.page_link()` throughout. Custom HTML anchor tags were considered and rejected because they open in a new tab and do not handle Streamlit's client-side routing correctly.
- The Unique Customers KPI on the Traffic and Conversion page queries COUNT(DISTINCT customer_id) directly from stg_events rather than relying on a pre-aggregated mart value.
- purchase_rate on the Traffic and Conversion page is calculated in Python as purchases divided by non-bounce events per source, not pre-computed in the mart model.
- expected_uplift values from dim_campaigns are multiplied by 100 in the Campaigns page before display. The source column stores decimals (e.g., 0.022), not percentages.
- The light theme is enforced via `.streamlit/config.toml`.
