with source as (
    select * from {{ source('dev', 'events') }}
),

renamed as (
    select
        event_id,
        timestamp::timestamp                        as event_timestamp,
        customer_id,
        session_id,
        lower(trim(event_type))                     as event_type,
        product_id,
        lower(trim(device_type))                    as device_type,
        coalesce(lower(trim(traffic_source)),
                 'unknown')                         as traffic_source,
        campaign_id,
        lower(trim(page_category))                  as page_category,
        session_duration_sec::double                as session_duration_sec,
        lower(trim(experiment_group))               as experiment_group,
        row_number() over (
            partition by event_id
            order by timestamp
        )                                           as row_num
    from source
    where session_id is not null
),

deduped as (
    select * from renamed where row_num = 1
)

select
    event_id,
    event_timestamp,
    customer_id,
    session_id,
    event_type,
    product_id,
    device_type,
    traffic_source,
    campaign_id,
    page_category,
    session_duration_sec,
    experiment_group
from deduped
