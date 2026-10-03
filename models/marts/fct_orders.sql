select
    o.*,
    e.category,
    e.category_group,
    e.day_type,
    e.event_date,
    e.market_name,
    e.is_fee_pilot_market
from {{ ref('int_orders_enriched') }} o
join {{ ref('int_events_enriched') }} e using (event_id, market_id)
