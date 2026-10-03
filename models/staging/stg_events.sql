select
    event_id,
    performer_id,
    venue_id,
    event_start_local,
    cast(event_start_local as date)                    as event_date,
    dayname(event_start_local)                         as event_day_name,
    -- Monday-Thursday shows are "weeknight"; Friday-Sunday are "weekend".
    case when isodow(event_start_local) between 1 and 4
         then 'weeknight' else 'weekend' end           as day_type,
    face_value,
    is_cancelled
from {{ source('raw', 'events') }}
