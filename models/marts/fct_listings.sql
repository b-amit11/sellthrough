select
    l.listing_id,
    l.event_id,
    l.seller_id,
    l.seat_zone,
    l.tickets_listed,
    l.list_price,
    round(l.list_price / nullif(e.face_value, 0), 3)          as price_to_face_ratio,
    l.listed_at,
    l.delisted_at,
    l.listing_status,
    l.listing_status = 'sold'                                  as is_sold,
    date_diff('day', l.listed_at, e.event_start_local)        as days_listed_before_event,
    e.market_id,
    e.category,
    e.day_type,
    e.event_date
from {{ ref('stg_listings') }} l
join {{ ref('int_events_enriched') }} e using (event_id)
