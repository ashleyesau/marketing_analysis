/*
  int_customer_cohorts
  --------------------
  Grain: one row per customer

  Computes cohort_month from signup_date only. Intentionally lightweight —
  no order metrics here. dim_customers and fct_cohort_retention join
  int_customer_orders directly for any revenue/order data.
*/

WITH customers AS (
    SELECT
        customer_id,
        signup_date,
        loyalty_tier,
        acquisition_channel,
        country
    FROM {{ ref('stg_customers') }}
)

SELECT
    customer_id,
    loyalty_tier,
    acquisition_channel,
    country,
    signup_date,
    DATE_TRUNC('month', signup_date) AS cohort_month
FROM customers
