/*
  fct_cohort_retention
  --------------------
  Grain: one row per cohort_month + order_month

  NOTE: Synthetic data artifact — some customers have signup_date after their
  first transaction date, producing negative months_since_signup values.
  These rows are excluded via WHERE months_since_signup >= 0 as they are
  meaningless for retention analysis.
*/

{{ config(materialized='table') }}

WITH cohorts AS (
    SELECT * FROM {{ ref('int_customer_cohorts') }}
),

transactions AS (
    SELECT * FROM {{ ref('fct_transactions') }}
)

SELECT
    c.cohort_month,
    DATE_TRUNC('month', t.transaction_timestamp)        AS order_month,
    DATEDIFF(
        'month',
        c.cohort_month,
        DATE_TRUNC('month', t.transaction_timestamp)
    )                                                   AS months_since_signup,
    COUNT(DISTINCT c.customer_id)                       AS active_customers,
    COUNT(DISTINCT t.transaction_id)                    AS total_orders,
    ROUND(SUM(t.gross_revenue), 2)                      AS total_revenue

FROM cohorts c
LEFT JOIN transactions t
    ON c.customer_id = t.customer_id

GROUP BY 1, 2, 3
HAVING months_since_signup >= 0
ORDER BY 1, 3
