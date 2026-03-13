with source as (
    select * from {{ source('dev', 'transactions') }}
),

renamed as (
    select
        transaction_id,
        timestamp::timestamp                        as transaction_timestamp,
        customer_id,
        product_id,
        quantity::integer                           as quantity,
        discount_applied::double                    as discount_applied,
        gross_revenue::double                       as gross_revenue,
        campaign_id,
        case when refund_flag = 1 then true
             else false
        end                                         as is_refunded,
        row_number() over (
            partition by transaction_id
            order by timestamp
        )                                           as row_num
    from source
),

deduped as (
    select * from renamed where row_num = 1
)

select
    transaction_id,
    transaction_timestamp,
    customer_id,
    product_id,
    quantity,
    discount_applied,
    gross_revenue,
    campaign_id,
    is_refunded
from deduped
