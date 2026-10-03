select
    performer_id,
    performer_name,
    performer_type,
    category,
    case when category in ('baseball', 'basketball', 'hockey', 'football') then 'sports'
         when category = 'concert' then 'concerts'
         else 'theater & comedy'
    end as category_group
from {{ source('raw', 'performers') }}
