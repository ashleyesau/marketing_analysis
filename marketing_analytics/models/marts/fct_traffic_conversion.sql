/*
  fct_traffic_conversion
  ----------------------
  Grain: one row per traffic_source + event_type

  Surfaces conversion rates by traffic source across all event types.
  Used by the Traffic & Conversion dashboard page.
  Source: stg_events (2M rows) — real signal confirmed in EDA.
*/

{{ config(materialized='table') }}

WITH events AS (
    SELECT
        traffic_source,
        event_type,
        customer_id
    FROM {{ ref('stg_events') }}
),

totals AS (
    SELECT
        traffic_source,
        COUNT(*) AS total_events
    FROM events
    GROUP BY 1
)

SELECT
    e.traffic_source,
    e.event_type,
    COUNT(*)                                                        AS event_count,
    COUNT(DISTINCT e.customer_id)                                   AS unique_customers,
    t.total_events,
    ROUND(COUNT(*) * 100.0 / t.total_events, 2)                    AS pct_of_traffic_events
FROM events e
JOIN totals t ON e.traffic_source = t.traffic_source
GROUP BY 1, 2, t.total_events
ORDER BY 1, 2
