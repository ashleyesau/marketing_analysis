WITH events AS (
    SELECT
        event_id,
        session_id,
        customer_id,
        event_type,
        event_timestamp,
        product_id,
        campaign_id
    FROM {{ ref('stg_events') }}
    WHERE event_type NOT IN ('bounce')
),

funnel_ranked AS (
    SELECT
        *,
        CASE event_type
            WHEN 'view'        THEN 1
            WHEN 'click'       THEN 2
            WHEN 'add_to_cart' THEN 3
            WHEN 'purchase'    THEN 4
        END AS funnel_step
    FROM events
)

SELECT
    event_id,
    session_id,
    customer_id,
    product_id,
    campaign_id,
    event_type,
    funnel_step,
    event_timestamp
FROM funnel_ranked
