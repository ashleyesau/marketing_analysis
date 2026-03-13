{{ config(materialized='table') }}

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT * FROM {{ ref('int_customer_orders') }}
),

cohorts AS (
    SELECT
        customer_id,
        cohort_month
    FROM {{ ref('int_customer_cohorts') }}
)

SELECT
    c.customer_id,
    c.age,
    c.gender,
    c.country,
    c.loyalty_tier,
    c.acquisition_channel,
    c.signup_date,
    ch.cohort_month,

    o.total_orders,
    o.total_items,
    o.total_revenue,
    o.avg_order_value,
    o.total_discount,
    o.total_refund_count,
    o.total_refund_value,
    o.first_order_date,
    o.last_order_date,

    CASE WHEN o.customer_id IS NOT NULL THEN 1 ELSE 0 END AS has_purchased

FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
LEFT JOIN cohorts ch
    ON c.customer_id = ch.customer_id
