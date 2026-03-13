with source as (
    select * from {{ source('dev', 'customers') }}
),

renamed as (
    select
        customer_id,
        signup_date::date                                        as signup_date,
        lower(trim(country))                                     as country,
        age,
        lower(trim(gender))                                      as gender,
        coalesce(lower(trim(loyalty_tier)), 'unknown')           as loyalty_tier,
        coalesce(lower(trim(acquisition_channel)), 'unknown')    as acquisition_channel
    from source
)

select * from renamed
