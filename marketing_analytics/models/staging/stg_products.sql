with source as (
    select * from {{ source('dev', 'products') }}
),

renamed as (
    select
        product_id,
        lower(trim(category))          as category,
        lower(trim(brand))             as brand,
        base_price::double             as base_price,
        launch_date::date              as launch_date,
        is_premium::boolean            as is_premium,
        row_number() over (
            partition by product_id
            order by launch_date
        )                              as row_num
    from source
),

deduped as (
    select * from renamed where row_num = 1
)

select
    product_id,
    category,
    brand,
    base_price,
    launch_date,
    is_premium
from deduped
