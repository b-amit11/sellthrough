-- One row per event with performer, venue, market and home-team form attached.
with events as (
    select * from {{ ref('stg_events') }}
),

performers as (
    select * from {{ ref('stg_performers') }}
),

venues as (
    select * from {{ ref('stg_venues') }}
),

markets as (
    select * from {{ ref('stg_markets') }}
),

home_games as (
    select team_id, game_date, last10_win_pct
    from {{ ref('stg_team_games') }}
    where is_home
)

select
    e.event_id,
    e.event_start_local,
    e.event_date,
    cast(date_trunc('month', e.event_date) as date) as event_month,
    e.event_day_name,
    e.day_type,
    e.face_value,
    e.is_cancelled,
    p.performer_id,
    p.performer_name,
    p.performer_type,
    p.category,
    p.category_group,
    v.venue_id,
    v.venue_name,
    v.venue_type,
    v.capacity,
    m.market_id,
    m.market_name,
    m.is_fee_pilot_market,
    hg.last10_win_pct                       as home_team_last10_win_pct
from events e
join performers p using (performer_id)
join venues v using (venue_id)
join markets m using (market_id)
left join home_games hg
    on hg.team_id = p.performer_id
   and hg.game_date = e.event_date
