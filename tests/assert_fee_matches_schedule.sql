-- The buyer fee charged on each order must match the fee schedule.
-- Tolerance covers a one-cent half-cent rounding difference between the source system and DuckDB.
select order_id, buyer_fee_amount, ticket_subtotal, buyer_fee_pct
from {{ ref('fct_orders') }}
where abs(buyer_fee_amount - ticket_subtotal * buyer_fee_pct) > 0.011
