select
    order_id,
    listing_id,
    event_id,
    buyer_id,
    quantity                                   as tickets_sold,
    ticket_price,
    round(ticket_price * quantity, 2)          as ticket_subtotal,
    buyer_fee_amount,
    seller_fee_amount,
    ordered_at,
    cast(ordered_at as date)                   as order_date,
    platform,
    order_status
from {{ source('raw', 'orders') }}
