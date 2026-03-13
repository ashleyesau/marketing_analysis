# Marketing Analytics Warehouse

An end-to-end analytics engineering project modeling customer segmentation, funnel analysis, product performance, and cohort retention on a synthetic e-commerce dataset.

---

## The Problem

Analytics engineering portfolios often demonstrate one or two patterns in isolation: a clean staging layer, a single mart, a simple dashboard. They rarely show how these pieces connect under real conditions, where data quality issues surface mid-project, where modeling decisions compound across layers, and where a metric that looks correct can be silently wrong due to a filter applied in the wrong order. The gap between knowing how dbt works and demonstrating that you can build a production-quality layered pipeline is exactly the kind of gap a portfolio project needs to close.

This project was built to fill that gap. The dataset is synthetic, but the problems it surfaces are genuine: a 10% null rate in the transactions table, refund signals split across two columns that behave differently, a campaign sentinel value masquerading as a foreign key, and a funnel model that produces plausible-looking output that turns out to be a data artifact with no analytical value.

## The Solution

The project builds a complete analytics engineering stack on a synthetic e-commerce dataset, from raw CSVs loaded via dbt seed through a three-layer transformation pipeline to a five-page Streamlit dashboard. It models customer lifetime value and cohort retention, traffic source conversion rates, product revenue performance, campaign attribution, and A/B experiment results. Every layer reflects deliberate decisions about data quality, grain, and naming convention: null revenue rows are excluded before aggregation, refund metrics are computed in a separate CTE before the revenue filter is applied, and a column naming conflict between customer acquisition channel and session-level traffic source is resolved rather than papered over.

The result is a warehouse and dashboard that a hiring manager can run locally or view on Streamlit Cloud, with a documented audit trail of every significant decision made along the way.

---

## Tech Stack

| Tool | Purpose | Why Chosen |
|---|---|---|
| DuckDB | Warehouse | No infrastructure required; handles 2M+ rows comfortably in-process on a local machine |
| dbt Core (dbt-duckdb) | Transformation | Industry-standard transformation layer; layered model architecture with built-in testing |
| Streamlit | Dashboard | Python-native; deploys to Streamlit Cloud without a separate server or container |
| Git + GitHub | Version control | Required for Streamlit Cloud deployment; clean orphan branch history avoids large file issues |
| Python 3 | Language | Native to every tool in the stack |

---

## Architecture

- Raw CSVs are loaded into DuckDB via `dbt seed`, creating five source tables in the dev schema
- `models/staging/` cleans, type-casts, and deduplicates each source table into five views
- `models/intermediate/` applies business logic: funnel step ranking, customer order aggregation, cohort assignment, cart activity tracking, and product-level funnel pivots
- `models/marts/` produces three dimension tables and seven fact tables as materialised DuckDB tables, pre-aggregated for fast Streamlit queries
- `pages/` contains the Streamlit app: a shared utilities module, a landing page, and four analysis pages that read directly from mart tables in `marketing.duckdb`
- `marketing.duckdb` is tracked in the repository so Streamlit Cloud can connect to it at runtime without running dbt

---

## Key Decisions

- DuckDB was chosen as the warehouse instead of a cloud platform. The full dataset (2M events, 100K customers, 103K transactions) runs comfortably in DuckDB's in-process columnar engine on a local machine, and the project constraint of a 2017 MacBook Air with no Docker or cloud infra made a zero-infrastructure setup essential. Modeling depth was the focus, not infrastructure management.

- 10,449 transactions with null product_id and gross_revenue (roughly 10% of the table) are excluded from all revenue models. EDA confirmed these rows are unresolvable at the source, not recoverable through joins or imputation. Including them would corrupt every downstream revenue aggregation silently, with no obvious sign that the numbers were wrong.

- The original Funnel Analysis dashboard page was replaced with a Traffic and Conversion page. The funnel segment model produced 419 rows with near-identical counts across every segment dimension, a synthetic data artifact with no analytical value. The events table (2M rows) contained real, meaningful variance in conversion rates by traffic source and experiment group, which became the foundation of the new page instead.

---

## Setup and Installation

Clone the repository and navigate into it:

```bash
git clone https://github.com/ashleyesau/marketing_analysis.git
cd marketing_analysis
```

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the Streamlit runtime dependencies:

```bash
pip install -r requirements.txt
```

To rebuild the warehouse from source, install dbt and the DuckDB adapter (not included in requirements.txt, which covers the Streamlit runtime only):

```bash
pip install dbt-duckdb
```

Supply the five seed CSVs (campaigns.csv, customers.csv, events.csv, products.csv, transactions.csv) in the `seeds/` directory. These are not tracked in the repository due to file size constraints. Anyone cloning the repo must provide their own copies to run dbt seed.

Load raw data and build all models:

```bash
dbt seed
dbt run
dbt test
```

Launch the dashboard locally:

```bash
streamlit run pages/app.py
```

The dashboard is also deployed to Streamlit Cloud at: Unknown (not stated)

---

## Results and Insights

- Electronics is the top revenue category at $3.55M over the three-year period, followed by Home ($2.05M), Fashion ($1.34M), and Sports ($1.00M)
- A consistent November and December revenue spike appears every year ($280-295K per month vs a $220K monthly average), suggesting seasonal purchasing patterns
- 36% of customers (35,965) have tracked events but never completed a transaction; the funnel drops sharply from view (52% of events) to purchase (5%)
- Email converts at 9.8% and paid search at 9.3%, both roughly four times the rate of organic and direct traffic (2.3% each)
- A/B experiment results show Variant B at a 12.2% purchase rate vs 9.0% for control (+3.2 percentage points); Variant A reaches 10.1% (+1.1pp)
- The loyalty base skews heavily Bronze (60%), with Silver at 25%, Gold at 12%, and Platinum at 3%
- 1,567 customers have at least one refund on record; total refund value is $152,314.65 across 2,704 full refunds and 325 partial refunds

---

## Sub-folder READMEs

- [models/staging](./marketing_analytics/models/staging/README.md) - Five staging models that clean and type-cast raw seed data before it enters the transformation pipeline
- [models/intermediate](./marketing_analytics/models/intermediate/README.md) - Five intermediate models computing funnel steps, customer order history, cohort assignments, and product-level metrics
- [models/marts](./marketing_analytics/models/marts/README.md) - Ten mart models producing the dimension tables and fact tables consumed by the dashboard
- [pages](./pages/README.md) - Streamlit dashboard with five pages covering customer segmentation, traffic conversion, product performance, campaign attribution, and A/B experiment results
