-- One row per event: supply, demand, funnel and economics.
with events as (
    select * from {{ ref('int_events_enriched') }}
),

listings as (
    select
        event_id,
        count(*)                                                     as listings,
        sum(tickets_listed)                                          as tickets_listed,
        sum(tickets_listed) filter (where listing_status = 'sold')   as tickets_sold,
        median(list_price)                                           as median_list_price
    from {{ ref('stg_listings') }}
    group by 1
),

orders as (
    select
        event_id,
        count(*)                                           as orders,
        count(*) filter (where is_fee_pilot_order)         as fee_pilot_orders,
        sum(gmv) filter (where is_completed)               as gmv,
        sum(net_revenue) filter (where is_completed)       as net_revenue,
        sum(ticket_subtotal) filter (where is_completed)   as ticket_sales
    from {{ ref('int_orders_enriched') }}
    group by 1
),

traffic as (
    select
        event_id,
        sum(sessions)          as sessions,
        sum(checkout_starts)   as checkout_starts
    from {{ ref('stg_event_traffic_daily') }}
    group by 1
)

select
    e.event_id,
    e.event_date,
    e.event_month,
    e.day_type,
    e.category,
    e.category_group,
    e.performer_name,
    e.market_id,
    e.market_name,
    e.is_fee_pilot_market,
    e.venue_name,
    e.capacity,
    e.is_cancelled,
    e.home_team_last10_win_pct,
    l.listings,
    l.tickets_listed,
    coalesce(l.tickets_sold, 0)                                         as tickets_sold,
    round(coalesce(l.tickets_sold, 0) / l.tickets_listed, 4)            as sell_through_rate,
    round(l.median_list_price, 2)                                       as median_list_price,
    coalesce(o.orders, 0)                                               as orders,
    coalesce(o.fee_pilot_orders, 0)                                     as fee_pilot_orders,
    round(coalesce(o.gmv, 0), 2)                                        as gmv,
    round(coalesce(o.net_revenue, 0), 2)                                as net_revenue,
    round(o.net_revenue / nullif(o.ticket_sales, 0), 4)                 as take_rate,
    coalesce(t.sessions, 0)                                             as sessions,
    coalesce(t.checkout_starts, 0)                                      as checkout_starts,
    round(t.checkout_starts / nullif(t.sessions, 0), 4)                 as session_to_checkout_rate,
    round(o.orders / nullif(t.checkout_starts, 0), 4)                   as checkout_to_order_rate
from events e
left join listings l using (event_id)
left join orders o using (event_id)
left join traffic t using (event_id)
