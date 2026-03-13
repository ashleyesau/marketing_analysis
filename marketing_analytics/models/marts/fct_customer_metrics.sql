{{ config(materialized='table') }}

WITH customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
)

SELECT
    customer_id,
    age,
    gender,
    country,
    loyalty_tier,
    acquisition_channel,
    signup_date,
    cohort_month,
    has_purchased,

    -- order metrics
    COALESCE(total_orders, 0)                          AS total_orders,
    COALESCE(total_items, 0)                           AS total_items,
    COALESCE(total_revenue, 0)                         AS total_revenue,
    avg_order_value,
    COALESCE(total_discount, 0)                        AS total_discount,
    COALESCE(total_refund_count, 0)                    AS total_refund_count,
    COALESCE(total_refund_value, 0)                    AS total_refund_value,
    first_order_date,
    last_order_date,

    -- derived LTV segments
    CASE
        WHEN total_revenue >= 1000 THEN 'high'
        WHEN total_revenue >= 300  THEN 'mid'
        WHEN total_revenue >= 1    THEN 'low'
        ELSE 'none'
    END AS ltv_segment

FROM customers
