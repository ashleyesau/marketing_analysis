/*
  int_customer_orders
  -------------------
  Grain: one row per customer

  total_revenue is intentionally GROSS (pre-refund). It sums gross_revenue
  from valid_purchases only (gross_revenue > 0), so full refunds (negative rows)
  are excluded from this figure. Refund value is tracked separately via
  total_refund_count and total_refund_value, calculated in the refunds CTE
  before the gross_revenue > 0 filter is applied.

  To calculate net revenue downstream: total_revenue - total_refund_value
*/

WITH transactions AS (
    SELECT
        transaction_id,
        customer_id,
        product_id,
        campaign_id,
        transaction_timestamp,
        quantity,
        gross_revenue,
        discount_applied,
        is_refunded
    FROM {{ ref('stg_transactions') }}
    WHERE product_id IS NOT NULL
      AND gross_revenue IS NOT NULL
),

valid_purchases AS (
    SELECT * FROM transactions
    WHERE gross_revenue > 0
),

refunds AS (
    SELECT
        customer_id,
        COUNT(transaction_id)               AS refund_count,
        ROUND(SUM(ABS(gross_revenue)), 2)   AS total_refund_value
    FROM transactions
    WHERE is_refunded = true
      AND gross_revenue < 0
    GROUP BY 1
)

SELECT
    p.customer_id,
    COUNT(p.transaction_id)                         AS total_orders,
    SUM(p.quantity)                                 AS total_items,
    ROUND(SUM(p.gross_revenue), 2)                  AS total_revenue,
    ROUND(AVG(p.gross_revenue), 2)                  AS avg_order_value,
    ROUND(SUM(p.discount_applied), 2)               AS total_discount,
    COALESCE(r.refund_count, 0)                     AS total_refund_count,
    COALESCE(r.total_refund_value, 0)               AS total_refund_value,
    MIN(p.transaction_timestamp)                    AS first_order_date,
    MAX(p.transaction_timestamp)                    AS last_order_date
FROM valid_purchases p
LEFT JOIN refunds r ON p.customer_id = r.customer_id
GROUP BY p.customer_id, r.refund_count, r.total_refund_value
