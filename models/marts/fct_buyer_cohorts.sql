-- Monthly buyer retention by first 2025 purchase month. Buyers active before 2025
-- land in the cohort of their first 2025 order, so January skews toward returning fans.
with buyer_months as (
    select distinct
        buyer_id,
        cast(date_trunc('month', order_date) as date) as order_month
    from {{ ref('int_orders_enriched') }}
    where is_completed
      and order_date >= date '2025-01-01'
),

firsts as (
    select buyer_id, min(order_month) as cohort_month
    from buyer_months
    group by 1
),

activity as (
    select
        f.cohort_month,
        date_diff('month', f.cohort_month, b.order_month) as months_since_first,
        count(distinct b.buyer_id)                         as active_buyers
    from buyer_months b
    join firsts f using (buyer_id)
    group by all
)

select
    cohort_month,
    months_since_first,
    active_buyers,
    first_value(active_buyers) over (
        partition by cohort_month order by months_since_first
    )                                                       as cohort_size,
    round(active_buyers / first_value(active_buyers) over (
        partition by cohort_month order by months_since_first
    ), 4)                                                   as retention_rate
from activity
