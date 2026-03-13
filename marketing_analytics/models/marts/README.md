# Marts Layer

Ten dbt models producing the dimension tables and fact tables that the Streamlit dashboard reads directly.

---

## Role in the Wider Project

- Final transformation layer in the marketing_analysis dbt pipeline
- Reads from intermediate views and, where intermediate joins would be redundant, from staging views directly
- All models are materialised as DuckDB tables for fast query performance in Streamlit
- The only layer the Streamlit app queries; no dashboard page reads staging or intermediate models

---

## What It Contains

Dimension tables:

- `dim_customers.sql` - One row per customer (100,000 rows); combines customer attributes from stg_customers, order metrics from int_customer_orders, and cohort_month from int_customer_cohorts via LEFT JOINs that preserve non-purchasers; includes has_purchased derived flag, acquisition_channel, total_refund_count, and total_refund_value
- `dim_products.sql` - One row per product (2,000 rows); combines product attributes from stg_products with funnel event counts from int_product_funnel via LEFT JOIN; products with no event history have NULL funnel metrics
- `dim_campaigns.sql` - One row per campaign (50 rows); pass-through from stg_campaigns with no additional transformations

Fact tables:

- `fct_transactions.sql` - One row per valid transaction (89,974 rows); excludes null product/revenue rows and full refund rows; converts campaign_id = 0 (the unattributed sentinel value) to NULL via NULLIF
- `fct_customer_metrics.sql` - One row per customer (100,000 rows); coalesces null order metrics to 0 for non-purchasers; derives ltv_segment (high >= $1,000, mid >= $300, low >= $1, none = never purchased)
- `fct_product_conversion.sql` - One row per product (2,000 rows); revenue metrics (total_transactions, unique_buyers, total_revenue, avg/min/max order_value, total_discount) aggregated directly from stg_transactions; funnel event counts joined from int_product_funnel; COALESCE 0 for products with no transactions
- `fct_cohort_retention.sql` - One row per cohort_month and order_month (666 rows); tracks revenue and order count per cohort over up to 35 months since signup; HAVING months_since_signup >= 0 removes 630 rows with negative values caused by a synthetic data artifact where signup_date was generated independently of transaction history
- `fct_traffic_conversion.sql` - One row per traffic_source and event_type (25 rows: 5 sources x 5 event types); event counts and customer counts per source; purchase rate calculated in the Streamlit page
- `fct_traffic_monthly.sql` - One row per traffic_source, event_month, and event_type (900 rows: 5 sources x 36 months x 5 event types); covers Jan 2021 to Dec 2023
- `fct_experiment_groups.sql` - One row per experiment_group (3 rows: control, variant_a, variant_b); purchase_rate, click_rate, add_to_cart_rate, and bounce_rate all expressed as a percentage of total views; null experiment_group rows filtered at source

- `schema.yml` - Column-level documentation and dbt tests for all ten models

---

## Inputs and Outputs

Inputs:

- `dev.stg_customers`, `dev.stg_transactions`, `dev.stg_events` - used directly where intermediate joins would be redundant
- `dev.int_customer_orders` - feeds dim_customers and fct_customer_metrics (via dim_customers)
- `dev.int_customer_cohorts` - feeds dim_customers
- `dev.int_product_funnel` - feeds dim_products and fct_product_conversion
- `dev.dim_customers` - feeds fct_customer_metrics

Outputs (all materialised as tables in the dev schema):

- `dev.dim_customers`
- `dev.dim_products`
- `dev.dim_campaigns`
- `dev.fct_transactions`
- `dev.fct_customer_metrics`
- `dev.fct_product_conversion`
- `dev.fct_cohort_retention`
- `dev.fct_traffic_conversion`
- `dev.fct_traffic_monthly`
- `dev.fct_experiment_groups`

---

## Notes

- `total_revenue` in fct_customer_metrics is intentionally gross (pre-refund), consistent with int_customer_orders. Net revenue = total_revenue - total_refund_value.
- fct_product_conversion was rebuilt from its original design, which sourced revenue from int_cart_activity. That model's session_id join never matched in the synthetic dataset, making total_cart_purchases permanently 0 for all 2,000 products. The rebuild sources revenue directly from stg_transactions and produces real variance (stddev $3,307, range $249-$33,310).
- campaign_id = 0 in fct_transactions is a sentinel value for unattributed transactions, not a genuine foreign key. It is converted to NULL via NULLIF so that unattributed rows do not incorrectly join to a campaign record.
- The expected_uplift column in dim_campaigns is stored as a decimal (e.g., 0.022 = 2.2%). The Streamlit pages multiply by 100 for percentage display.
- There is no product_name or campaign_name in the source data. Products and campaigns are identified by their ID, category/brand, and channel/objective respectively.
