connection: "sellthrough_warehouse"

include: "/views/*.view.lkml"

datagroup: nightly {
  sql_trigger: SELECT CURRENT_DATE ;;
  max_cache_age: "24 hours"
}
persist_with: nightly

explore: event_performance {
  label: "Event Performance"
  description: "One row per event: supply, funnel and economics."
}

explore: market_daily {
  label: "Daily Market Trends"
  description: "Sessions, checkouts, orders and revenue by activity date."
}
