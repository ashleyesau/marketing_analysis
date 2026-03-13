/*
  fct_traffic_monthly
  -------------------
  Grain: one row per traffic_source + month + event_type

  Tracks event volume over time by traffic source and event type.
  Used by the Traffic & Conversion dashboard page for trend charts.
  Source: stg_events (2M rows).
*/

{{ config(materialized='table') }}

WITH events AS (
    SELECT
        traffic_source,
        event_type,
        customer_id,
        DATE_TRUNC('month', event_timestamp) AS event_month
    FROM {{ ref('stg_events') }}
)

SELECT
    traffic_source,
    event_month,
    event_type,
    COUNT(*)                        AS event_count,
    COUNT(DISTINCT customer_id)     AS unique_customers
FROM events
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
