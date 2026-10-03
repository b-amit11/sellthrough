# Building the Data Studio dashboard

**Live dashboard:** [Sellthrough – Fee Pilot Dashboard](https://datastudio.google.com/reporting/f2f08fb4-7c2d-40a7-9f75-b5ff42d51ef0)

Data Studio (formerly Looker Studio) is free with a Google account. These steps rebuild the dashboard from the CSVs in `exports/`.

## 1. Load the data

1. Create a blank report and choose the **CSV File Upload** connector.
2. Upload each CSV into **its own dataset**: `event_performance`, `market_daily`, `buyer_cohorts`. A dataset only accepts files with identical columns, so putting two different CSVs in one fails with "Invalid column header name(s)".

## 2. Fix the date fields

Data Studio detects the `YYYY-MM-DD` columns as text, and switching their type to Date fails or silently produces nulls ("Can't convert to date", or a chart that goes empty once a date range is applied). The reliable fix is to leave the column as **Text** and add a parsed copy:

| Data source | Field | Formula |
|---|---|---|
| market_daily | `Week date` | `PARSE_DATE("%Y-%m-%d", activity_date)` |
| event_performance | `Event date` | `PARSE_DATE("%Y-%m-%d", event_date)` |

Use these calculated fields wherever a chart needs a date dimension or a date range.

## 3. Add the rate fields

Rates must be a ratio of sums. An average of per-event rates would weight a 20-ticket comedy show the same as a 2,000-ticket ballgame. Set each one's type to **Percent**.

| Data source | Field | Formula |
|---|---|---|
| event_performance | `Sell-through` | `SUM(tickets_sold) / SUM(tickets_listed)` |
| event_performance | `Checkout → order` | `SUM(orders) / SUM(checkout_starts)` |
| market_daily | `Checkout → order` | `SUM(orders) / SUM(checkout_starts)` |

## 4. Charts

**Checkout conversion by week** (the headline)
- Time series · data source `market_daily`
- Dimension `Week date` at **ISO Year Week** granularity · breakdown `is_fee_pilot_market` · metric `Checkout → order`
- Date range dimension `Week date`, fixed range Apr 7 – Nov 30, 2025

**Sell-through by day type, after the pilot started**
- Column chart · data source `event_performance`
- Dimension `day_type` · breakdown `is_fee_pilot_market` · metric `Sell-through`
- Date range dimension `Event date`, fixed range Aug 8 – Sep 30, 2025

Give each chart a text-box title that says what it shows and that `true` means a pilot market with the 20% buyer fee.

## 5. Share

**Share → Link settings → Unlisted or Public, Viewer.** The data is synthetic, so a public link is safe.
