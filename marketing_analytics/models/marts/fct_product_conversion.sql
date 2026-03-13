/*
  fct_product_conversion
  ----------------------
  Grain: one row per product_id

  Rebuilt to source revenue from stg_transactions — original model relied on
  int_cart_activity which uses session_id join; cart and purchase events never
  share session_ids in this dataset so total_cart_purchases was always 0.

  Funnel metrics (views, clicks, add_to_carts, purchases) retained from
  int_product_funnel as event counts. Revenue and transaction metrics
  sourced directly from stg_transactions.
*/

{{ config(materialized='table') }}

WITH product_funnel AS (
    SELECT * FROM {{ ref('int_product_funnel') }}
),

product_revenue AS (
    SELECT
        product_id,
        COUNT(DISTINCT transaction_id)              AS total_transactions,
        COUNT(DISTINCT customer_id)                 AS unique_buyers,
        ROUND(SUM(gross_revenue), 2)                AS total_revenue,
        ROUND(AVG(gross_revenue), 2)                AS avg_order_value,
        ROUND(MIN(gross_revenue), 2)                AS min_order_value,
        ROUND(MAX(gross_revenue), 2)                AS max_order_value,
        ROUND(SUM(discount_applied), 2)             AS total_discount
    FROM {{ ref('stg_transactions') }}
    WHERE gross_revenue > 0
      AND product_id IS NOT NULL
    GROUP BY 1
),

products AS (
    SELECT
        product_id,
        category,
        brand,
        base_price
    FROM {{ ref('dim_products') }}
)

SELECT
    p.product_id,
    p.category,
    p.brand,
    p.base_price,

    -- funnel event counts
    pf.views,
    pf.clicks,
    pf.add_to_carts,
    pf.purchases,
    pf.view_to_click_pct,
    pf.click_to_cart_pct,
    pf.cart_to_purchase_pct,
    pf.overall_conversion_pct,

    -- transaction revenue metrics
    COALESCE(pr.total_transactions, 0)  AS total_transactions,
    COALESCE(pr.unique_buyers, 0)       AS unique_buyers,
    COALESCE(pr.total_revenue, 0)       AS total_revenue,
    COALESCE(pr.avg_order_value, 0)     AS avg_order_value,
    COALESCE(pr.min_order_value, 0)     AS min_order_value,
    COALESCE(pr.max_order_value, 0)     AS max_order_value,
    COALESCE(pr.total_discount, 0)      AS total_discount

FROM products p
LEFT JOIN product_funnel pf   ON p.product_id = pf.product_id
LEFT JOIN product_revenue pr  ON p.product_id = pr.product_id
