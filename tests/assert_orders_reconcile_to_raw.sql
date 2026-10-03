-- Every raw order must survive the fee-schedule join exactly once.
select
    (select count(*) from {{ source('raw', 'orders') }})  as raw_orders,
    (select count(*) from {{ ref('fct_orders') }})        as modelled_orders
where raw_orders != modelled_orders
