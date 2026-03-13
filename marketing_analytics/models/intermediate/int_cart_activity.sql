WITH cart_events AS (
    SELECT
        session_id,
        customer_id,
        product_id,
        campaign_id,
        event_timestamp
    FROM {{ ref('stg_events') }}
    WHERE event_type = 'add_to_cart'
),

purchases AS (
    SELECT
        session_id,
        customer_id,
        product_id
    FROM {{ ref('stg_events') }}
    WHERE event_type = 'purchase'
)

SELECT
    c.session_id,
    c.customer_id,
    c.product_id,
    c.campaign_id,
    c.event_timestamp AS added_to_cart_at,
    CASE WHEN p.product_id IS NOT NULL THEN 1 ELSE 0 END AS was_purchased
FROM cart_events c
LEFT JOIN purchases p
    ON c.session_id = p.session_id
    AND c.customer_id = p.customer_id
    AND c.product_id = p.product_id
