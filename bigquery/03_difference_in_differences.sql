-- Pooled difference-in-differences on weeknight sell-through:
-- (pilot post - pilot pre) - (control post - control pre).
-- The memo's regression with fixed effects gives -8.7 points; this pooled version is a quick check.
WITH events AS (
  SELECT
    is_fee_pilot_market,
    tickets_sold,
    tickets_listed,
    CASE
      WHEN event_date BETWEEN '2025-06-01' AND '2025-07-25' THEN 'pre'
      WHEN event_date BETWEEN '2025-08-08' AND '2025-09-30' THEN 'post'
    END AS period
  FROM `sellthrough.fct_event_performance`
  WHERE NOT is_cancelled
    AND day_type = 'weeknight'
    AND NOT (market_name = 'Phoenix' AND category = 'baseball')
),
rates AS (
  SELECT
    is_fee_pilot_market,
    period,
    SAFE_DIVIDE(SUM(tickets_sold), SUM(tickets_listed)) AS sell_through
  FROM events
  WHERE period IS NOT NULL
  GROUP BY is_fee_pilot_market, period
)
SELECT
  ROUND(MAX(IF(is_fee_pilot_market AND period = 'post', sell_through, NULL))
      - MAX(IF(is_fee_pilot_market AND period = 'pre', sell_through, NULL)), 4)      AS pilot_change,
  ROUND(MAX(IF(NOT is_fee_pilot_market AND period = 'post', sell_through, NULL))
      - MAX(IF(NOT is_fee_pilot_market AND period = 'pre', sell_through, NULL)), 4)  AS control_change,
  ROUND((MAX(IF(is_fee_pilot_market AND period = 'post', sell_through, NULL))
       - MAX(IF(is_fee_pilot_market AND period = 'pre', sell_through, NULL)))
      - (MAX(IF(NOT is_fee_pilot_market AND period = 'post', sell_through, NULL))
       - MAX(IF(NOT is_fee_pilot_market AND period = 'pre', sell_through, NULL))), 4) AS diff_in_diff
FROM rates;
