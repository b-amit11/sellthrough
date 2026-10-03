select
    buyer_id,
    home_market_id,
    signup_date
from {{ source('raw', 'buyers') }}
