{{ config(materialized='table') }}

WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

funnel AS (
    SELECT * FROM {{ ref('int_product_funnel') }}
)

SELECT
    p.product_id,
    p.category,
    p.brand,
    p.base_price,
    p.launch_date,
    p.is_premium,
    f.views,
    f.clicks,
    f.add_to_carts,
    f.purchases,
    f.view_to_click_pct,
    f.click_to_cart_pct,
    f.cart_to_purchase_pct,
    f.overall_conversion_pct

FROM products p
LEFT JOIN funnel f
    ON p.product_id = f.product_id
