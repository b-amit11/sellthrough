-- Daily activity by market and category group, dated by when the activity happened
-- (session or order date), not by event date. Used for trend dashboards.
with traffic as (
    select
        t.activity_date                as activity_date,
        e.market_id,
        e.category_group,
        e.day_type,
        sum(t.sessions)                as sessions,
        sum(t.checkout_starts)         as checkout_starts
    from {{ ref('stg_event_traffic_daily') }} t
    join {{ ref('int_events_enriched') }} e using (event_id)
    group by all
),

orders as (
    select
        o.order_date                                         as activity_date,
        o.market_id,
        e.category_group,
        e.day_type,
        count(*)                                             as orders,
        sum(o.tickets_sold)                                  as tickets_sold,
        sum(o.gmv) filter (where o.is_completed)             as gmv,
        sum(o.net_revenue) filter (where o.is_completed)     as net_revenue
    from {{ ref('int_orders_enriched') }} o
    join {{ ref('int_events_enriched') }} e using (event_id)
    group by all
)

select
    activity_date,
    market_id,
    m.market_name,
    m.is_fee_pilot_market,
    category_group,
    day_type,
    coalesce(t.sessions, 0)          as sessions,
    coalesce(t.checkout_starts, 0)   as checkout_starts,
    coalesce(o.orders, 0)            as orders,
    coalesce(o.tickets_sold, 0)      as tickets_sold,
    coalesce(o.gmv, 0)               as gmv,
    coalesce(o.net_revenue, 0)       as net_revenue
from traffic t
full outer join orders o using (activity_date, market_id, category_group, day_type)
join {{ ref('stg_markets') }} m using (market_id)
where activity_date between date '2025-01-01' and date '2025-12-31'
