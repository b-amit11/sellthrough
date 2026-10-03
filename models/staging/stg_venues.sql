select
    venue_id,
    venue_name,
    market_id,
    venue_type,
    capacity
from {{ source('raw', 'venues') }}
