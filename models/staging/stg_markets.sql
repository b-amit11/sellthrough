select
    market_id,
    market_name,
    state,
    is_fee_pilot_market
from {{ source('raw', 'markets') }}
