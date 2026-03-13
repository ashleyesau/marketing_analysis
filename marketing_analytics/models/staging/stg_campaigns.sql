with source as (
    select * from {{ source('dev', 'campaigns') }}
),

renamed as (
    select
        campaign_id,
        lower(trim(channel))           as channel,
        lower(trim(objective))         as objective,
        start_date::date               as start_date,
        end_date::date                 as end_date,
        lower(trim(target_segment))    as target_segment,
        expected_uplift::double        as expected_uplift
    from source
)

select * from renamed
