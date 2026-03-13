# Intermediate Layer

Five dbt models that apply business logic on top of staging views, computing funnel step rankings, customer order history, cohort assignments, cart activity, and product-level funnel metrics.

---

## Role in the Wider Project

- Second transformation layer in the marketing_analysis dbt pipeline
- All five models source from staging views only; no intermediate model reads raw seed tables directly
- Provides the reusable building blocks consumed by mart models; no intermediate model is queried by the Streamlit dashboard directly
- Isolates complex logic (session-level joins, refund accounting, cohort derivation, funnel pivots) so that mart models can stay clean and declarative

---

## What It Contains

- `int_funnel_steps.sql` - Filters out bounce events and ranks each remaining event as a numbered funnel step (view=1, click=2, add_to_cart=3, purchase=4); bounce exclusion is intentional because bounces are exits, not progression steps
- `int_cart_activity.sql` - Tracks each add_to_cart event and attempts to join to a subsequent purchase event in the same session; the was_purchased flag is always 0 in this dataset because cart and purchase events never share session_ids (confirmed via query: 0 matching sessions out of 2M events); retained in the warehouse as a documented synthetic data artifact but not surfaced in the dashboard
- `int_customer_orders.sql` - Aggregates transaction history per customer using three CTEs: all non-null product/revenue rows, valid purchases (gross_revenue > 0), and refunds (is_refunded=true, gross_revenue < 0); refund metrics are computed before the gross_revenue > 0 filter is applied so they are not silently zeroed out; produces one row per purchasing customer with total_revenue (gross), total_refund_count, total_refund_value, order counts, and first/last order dates
- `int_customer_cohorts.sql` - Assigns each customer a signup cohort month via DATE_TRUNC('month', signup_date); lightweight model that sources only from stg_customers; no order metrics computed here (all order metrics flow through dim_customers via int_customer_orders)
- `int_product_funnel.sql` - Pivots event counts per product using MAX(CASE WHEN) and computes step conversion rates (view_to_click_pct, click_to_cart_pct, cart_to_purchase_pct, overall_conversion_pct) using NULLIF to avoid division by zero; conversion rates are uniform across all categories (approx. 8.9%) due to the synthetic dataset and are not used for category-level analysis in the dashboard
- `schema.yml` - Column-level documentation and dbt tests for all five models

---

## Inputs and Outputs

Inputs:

- `dev.stg_events` - used by int_funnel_steps, int_cart_activity
- `dev.stg_transactions` - used by int_customer_orders
- `dev.stg_customers` - used by int_customer_cohorts
- `dev.int_funnel_steps` - used by int_product_funnel

Outputs (all materialised as views in the dev schema):

- `dev.int_funnel_steps`
- `dev.int_cart_activity`
- `dev.int_customer_orders`
- `dev.int_customer_cohorts`
- `dev.int_product_funnel`

---

## Notes

- `total_revenue` in int_customer_orders is intentionally gross (pre-refund). Net revenue per customer = total_revenue - total_refund_value. This distinction is documented in the model header.
- 10,449 transactions with null product_id and null gross_revenue are excluded before aggregation. These rows are unresolvable at the source and including them would corrupt all revenue metrics downstream.
- int_customer_cohorts was simplified from its original design, which joined int_customer_orders internally and created a redundant dependency path. It now sources only from stg_customers and contributes only cohort_month to the mart layer.
- int_cart_activity is retained so the model and its documented limitation remain visible. It is not referenced by any dashboard page.
