-- Weekly checkout conversion, pilot vs. control markets.
-- The fee pilot starts 2025-08-01; pilot markets should drop from ~44% to ~40%.
SELECT
  DATE_TRUNC(activity_date, ISOWEEK)                     AS week,
  IF(is_fee_pilot_market, 'Pilot (20% fee)', 'Control (15% fee)') AS market_group,
  SUM(checkout_starts)                                   AS checkout_starts,
  SUM(orders)                                            AS orders,
  ROUND(SAFE_DIVIDE(SUM(orders), SUM(checkout_starts)), 4) AS checkout_to_order
FROM `sellthrough.fct_market_daily`
WHERE activity_date BETWEEN '2025-04-07' AND '2025-11-30'
GROUP BY week, market_group
ORDER BY week, market_group;
