{{ config(materialized='table') }}

-- Grain: one row per experiment_group
-- Purchase rate = purchase events / view events (consistent with fct_traffic_conversion)
-- Source: stg_events only — experiment_group is an event-level field

WITH base AS (
    SELECT
        experiment_group,
        COUNT_IF(event_type = 'view')         AS total_views,
        COUNT_IF(event_type = 'click')        AS total_clicks,
        COUNT_IF(event_type = 'add_to_cart')  AS total_add_to_cart,
        COUNT_IF(event_type = 'purchase')     AS total_purchases,
        COUNT_IF(event_type = 'bounce')       AS total_bounces,
        COUNT(DISTINCT customer_id)           AS total_customers
    FROM {{ ref('stg_events') }}
    WHERE experiment_group IS NOT NULL
    GROUP BY 1
)

SELECT
    experiment_group,
    total_views,
    total_clicks,
    total_add_to_cart,
    total_purchases,
    total_bounces,
    total_customers,
    ROUND(total_purchases * 100.0 / NULLIF(total_views, 0), 2)        AS purchase_rate,
    ROUND(total_clicks    * 100.0 / NULLIF(total_views, 0), 2)        AS click_rate,
    ROUND(total_add_to_cart * 100.0 / NULLIF(total_views, 0), 2)      AS add_to_cart_rate,
    ROUND(total_bounces   * 100.0 / NULLIF(total_views, 0), 2)        AS bounce_rate
FROM base
ORDER BY experiment_group
