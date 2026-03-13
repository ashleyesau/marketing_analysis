WITH funnel AS (
    SELECT
        product_id,
        event_type,
        COUNT(*) AS event_count
    FROM {{ ref('int_funnel_steps') }}
    WHERE product_id IS NOT NULL
    GROUP BY 1, 2
)

SELECT
    product_id,
    MAX(CASE WHEN event_type = 'view'        THEN event_count ELSE 0 END) AS views,
    MAX(CASE WHEN event_type = 'click'       THEN event_count ELSE 0 END) AS clicks,
    MAX(CASE WHEN event_type = 'add_to_cart' THEN event_count ELSE 0 END) AS add_to_carts,
    MAX(CASE WHEN event_type = 'purchase'    THEN event_count ELSE 0 END) AS purchases,
    ROUND(
        MAX(CASE WHEN event_type = 'click' THEN event_count ELSE 0 END) * 100.0 /
        NULLIF(MAX(CASE WHEN event_type = 'view' THEN event_count ELSE 0 END), 0), 2
    ) AS view_to_click_pct,
    ROUND(
        MAX(CASE WHEN event_type = 'add_to_cart' THEN event_count ELSE 0 END) * 100.0 /
        NULLIF(MAX(CASE WHEN event_type = 'click' THEN event_count ELSE 0 END), 0), 2
    ) AS click_to_cart_pct,
    ROUND(
        MAX(CASE WHEN event_type = 'purchase' THEN event_count ELSE 0 END) * 100.0 /
        NULLIF(MAX(CASE WHEN event_type = 'add_to_cart' THEN event_count ELSE 0 END), 0), 2
    ) AS cart_to_purchase_pct,
    ROUND(
        MAX(CASE WHEN event_type = 'purchase' THEN event_count ELSE 0 END) * 100.0 /
        NULLIF(MAX(CASE WHEN event_type = 'view' THEN event_count ELSE 0 END), 0), 2
    ) AS overall_conversion_pct
FROM funnel
GROUP BY 1
