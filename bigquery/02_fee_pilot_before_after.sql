-- Before/after comparison by market group and day type: the raw inputs to the
-- difference-in-differences estimate in reports/memo.md.
-- Excludes Phoenix baseball, whose August slump would otherwise inflate the fee effect.
WITH events AS (
  SELECT
    *,
    CASE
      WHEN event_date BETWEEN '2025-06-01' AND '2025-07-25' THEN 'pre'
      WHEN event_date BETWEEN '2025-08-08' AND '2025-09-30' THEN 'post'
    END AS period
  FROM `sellthrough.fct_event_performance`
  WHERE NOT is_cancelled
    AND NOT (market_name = 'Phoenix' AND category = 'baseball')
)
SELECT
  day_type,
  IF(is_fee_pilot_market, 'Pilot', 'Control')                    AS market_group,
  period,
  COUNT(*)                                                       AS events,
  ROUND(SAFE_DIVIDE(SUM(tickets_sold), SUM(tickets_listed)), 4)  AS sell_through,
  ROUND(SAFE_DIVIDE(SUM(orders), SUM(checkout_starts)), 4)       AS checkout_to_order
FROM events
WHERE period IS NOT NULL
GROUP BY day_type, market_group, period
ORDER BY day_type, market_group, period DESC;
