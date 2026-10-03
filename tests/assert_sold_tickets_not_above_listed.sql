-- An event can never sell more tickets than were listed for it.
select event_id, tickets_listed, tickets_sold
from {{ ref('fct_event_performance') }}
where tickets_sold > tickets_listed
