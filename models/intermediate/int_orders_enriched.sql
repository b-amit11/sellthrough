-- Orders with marketplace economics and the fee regime in force when the order was placed.
with orders as (
    select * from {{ ref('stg_orders') }}
),

events as (
    select event_id, market_id, event_start_local from {{ ref('int_events_enriched') }}
),

fees as (
    select * from {{ ref('stg_fee_schedule') }}
)

select
    o.order_id,
    o.listing_id,
    o.event_id,
    o.buyer_id,
    e.market_id,
    o.ordered_at,
    o.order_date,
    date_diff('day', o.ordered_at, e.event_start_local)       as days_before_event,
    o.platform,
    o.order_status,
    o.order_status = 'completed'                               as is_completed,
    o.tickets_sold,
    o.ticket_price,
    o.ticket_subtotal,
    o.buyer_fee_amount,
    o.seller_fee_amount,
    f.buyer_fee_pct,
    f.buyer_fee_pct > 0.15                                     as is_fee_pilot_order,
    -- GMV is what the buyer pays: tickets plus the buyer fee.
    o.ticket_subtotal + o.buyer_fee_amount                     as gmv,
    -- Net revenue is what the marketplace keeps from both sides.
    o.buyer_fee_amount + o.seller_fee_amount                   as net_revenue
from orders o
join events e using (event_id)
join fees f
    on f.market_id = e.market_id
   and o.order_date between f.effective_from and f.effective_to
