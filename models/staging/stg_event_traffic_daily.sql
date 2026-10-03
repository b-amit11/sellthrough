select
    event_id,
    activity_date,
    sessions,
    checkout_starts
from {{ source('raw', 'event_traffic_daily') }}
