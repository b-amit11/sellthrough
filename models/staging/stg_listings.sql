select
    listing_id,
    event_id,
    seller_id,
    seat_zone,
    quantity          as tickets_listed,
    list_price,
    listed_at,
    delisted_at,
    listing_status
from {{ source('raw', 'listings') }}
