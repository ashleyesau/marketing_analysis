{{ config(materialized='table') }}

WITH transactions AS (
    SELECT * FROM {{ ref('stg_transactions') }}
)

SELECT
    t.transaction_id,
    t.customer_id,
    t.product_id,
    t.transaction_timestamp,
    t.quantity,
    t.gross_revenue,
    t.discount_applied,
    t.is_refunded,
    NULLIF(t.campaign_id, 0) AS campaign_id

FROM transactions t
WHERE t.product_id IS NOT NULL
  AND t.gross_revenue IS NOT NULL
  AND t.gross_revenue > 0
