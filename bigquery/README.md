# BigQuery

The mart extracts in `exports/` are loaded into Google BigQuery (free sandbox) as
`sellthrough.fct_market_daily` and `sellthrough.fct_event_performance`, and the queries
below run against them in BigQuery standard SQL.

| Query | What it answers |
|---|---|
| [`01_weekly_checkout_conversion.sql`](01_weekly_checkout_conversion.sql) | Weekly checkout conversion, pilot vs. control (feeds the Tableau chart) |
| [`02_fee_pilot_before_after.sql`](02_fee_pilot_before_after.sql) | Sell-through and checkout conversion before vs. after the pilot, by day type |
| [`03_difference_in_differences.sql`](03_difference_in_differences.sql) | Pooled difference-in-differences on weeknight sell-through |

The before/after comparison (the weeknight rows of `02`) has been run in BigQuery and matches
the DuckDB warehouse exactly: for example, control-market weeknight sell-through before the
pilot is 0.5745 and checkout conversion 0.4385 in both.

## Load the data yourself

1. In the BigQuery console, create a dataset named `sellthrough` (US multi-region).
2. **Create table → Upload**, pick `exports/fct_market_daily.csv`, name the table
   `fct_market_daily`, tick **Auto detect**. Repeat for `fct_event_performance.csv`.
3. Open a query tab and run any file in this folder.
