select
    market_id,
    cast(effective_from as date) as effective_from,
    cast(effective_to as date)   as effective_to,
    buyer_fee_pct,
    seller_fee_pct
from {{ source('raw', 'fee_schedule') }}
