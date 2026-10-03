select
    m.market_id,
    m.market_name,
    m.state,
    m.is_fee_pilot_market,
    count(v.venue_id)   as venue_count,
    sum(v.capacity)     as total_capacity
from {{ ref('stg_markets') }} m
left join {{ ref('stg_venues') }} v using (market_id)
group by all
