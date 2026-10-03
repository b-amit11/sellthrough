# Building the Looker Studio dashboard

Looker Studio is free with a Google account. These steps build a two-page dashboard from the CSVs in `exports/`.

## 1. Load the data

1. Open [lookerstudio.google.com](https://lookerstudio.google.com) and create a **Blank report**.
2. Choose **File upload** as the connector and upload `exports/fct_event_performance.csv`.
3. Add two more data sources the same way: `fct_market_daily.csv` and `fct_buyer_cohorts.csv`.
4. In each source, check the field types: dates as **Date**, `is_fee_pilot_market` as **Boolean**, and rates as **Percent**.

## 2. Add calculated fields

Rates must be a ratio of sums. An average of per-event rates would weight a 20-ticket comedy show the same as a 2,000-ticket ballgame.

In `fct_event_performance`:

| Field | Formula | Type |
|---|---|---|
| Sell-through | `SUM(tickets_sold) / SUM(tickets_listed)` | Percent |
| Checkout → order | `SUM(orders) / SUM(checkout_starts)` | Percent |
| Session → checkout | `SUM(checkout_starts) / SUM(sessions)` | Percent |
| Revenue per listed ticket | `SUM(net_revenue) / SUM(tickets_listed)` | Currency |
| Pilot group | `CASE WHEN is_fee_pilot_market THEN "Pilot (20% fee from Aug 1)" ELSE "Control (15%)" END` | Text |

In `fct_market_daily`:

| Field | Formula | Type |
|---|---|---|
| Checkout → order | `SUM(orders) / SUM(checkout_starts)` | Percent |
| Pilot group | same as above | Text |

## 3. Page 1: Marketplace health

- **Scorecards across the top** (`fct_market_daily`): GMV, Net revenue, Orders, Checkout → order. Turn on **comparison to previous period**.
- **Time series** (`fct_market_daily`): GMV by week, broken down by `category_group`.
- **Table** (`fct_event_performance`): rows = `market_name`; columns = Sell-through, Checkout → order, GMV, Net revenue. Add a heatmap on Sell-through.
- **Controls:** date range, `category_group`, `day_type`, `market_name`.

## 4. Page 2: Fee pilot readout

- **Time series** (`fct_market_daily`): Checkout → order by week, breakdown = Pilot group. Add a reference line at Aug 1. This is the headline chart.
- **Bar chart** (`fct_event_performance`): Sell-through by `day_type`, breakdown = Pilot group. Filter to events after Aug 8.
- **Scatter** (`fct_event_performance`): filter `performer_name = Phoenix Scorpions`; x = `event_date`, y = `sessions`, bubble color = `home_team_last10_win_pct`. This shows the slump that confounds the pilot.
- **Text box:** paste the three-line recommendation from `reports/memo.md`.

## 5. Page 3 (optional): Retention

- **Pivot table** (`fct_buyer_cohorts`): rows = `cohort_month`, columns = `months_since_first`, metric = `retention_rate` with a heatmap. This is a standard cohort triangle.

## 6. Share it

**Share → Manage access → Anyone with the link can view.** Put the link at the top of the README.
