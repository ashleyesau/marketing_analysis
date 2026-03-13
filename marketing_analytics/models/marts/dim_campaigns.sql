{{ config(materialized='table') }}

WITH campaigns AS (
    SELECT * FROM {{ ref('stg_campaigns') }}
)

SELECT
    campaign_id,
    channel,
    objective,
    target_segment,
    start_date,
    end_date,
    expected_uplift

FROM campaigns
WHERE campaign_id != 0
