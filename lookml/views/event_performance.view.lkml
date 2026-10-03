view: event_performance {
  sql_table_name: main.fct_event_performance ;;

  dimension: event_id {
    primary_key: yes
    type: number
    sql: ${TABLE}.event_id ;;
  }

  dimension_group: event {
    type: time
    timeframes: [date, week, month, quarter]
    datatype: date
    sql: ${TABLE}.event_date ;;
  }

  dimension: day_type {
    description: "weeknight = Mon-Thu, weekend = Fri-Sun"
    sql: ${TABLE}.day_type ;;
  }

  dimension: category { sql: ${TABLE}.category ;; }
  dimension: category_group { sql: ${TABLE}.category_group ;; }
  dimension: performer_name { sql: ${TABLE}.performer_name ;; }
  dimension: market_name { sql: ${TABLE}.market_name ;; }
  dimension: venue_name { sql: ${TABLE}.venue_name ;; }

  dimension: is_fee_pilot_market {
    type: yesno
    sql: ${TABLE}.is_fee_pilot_market ;;
  }

  dimension: is_cancelled {
    type: yesno
    sql: ${TABLE}.is_cancelled ;;
  }

  dimension: home_team_last10_win_pct {
    type: number
    value_format_name: decimal_3
    sql: ${TABLE}.home_team_last10_win_pct ;;
  }

  measure: events {
    type: count
  }

  measure: tickets_listed {
    type: sum
    sql: ${TABLE}.tickets_listed ;;
  }

  measure: tickets_sold {
    type: sum
    sql: ${TABLE}.tickets_sold ;;
  }

  measure: sell_through_rate {
    description: "Tickets sold / tickets listed. Ratio of sums, not an average of event rates."
    type: number
    value_format_name: percent_1
    sql: 1.0 * ${tickets_sold} / NULLIF(${tickets_listed}, 0) ;;
  }

  measure: orders {
    type: sum
    sql: ${TABLE}.orders ;;
  }

  measure: sessions {
    type: sum
    sql: ${TABLE}.sessions ;;
  }

  measure: checkout_starts {
    type: sum
    sql: ${TABLE}.checkout_starts ;;
  }

  measure: session_to_checkout_rate {
    type: number
    value_format_name: percent_1
    sql: 1.0 * ${checkout_starts} / NULLIF(${sessions}, 0) ;;
  }

  measure: checkout_to_order_rate {
    description: "Where buyer fee changes show up: buyers see the fee at checkout."
    type: number
    value_format_name: percent_1
    sql: 1.0 * ${orders} / NULLIF(${checkout_starts}, 0) ;;
  }

  measure: gmv {
    label: "GMV"
    description: "Ticket subtotal plus buyer fee, completed orders."
    type: sum
    value_format_name: usd_0
    sql: ${TABLE}.gmv ;;
  }

  measure: net_revenue {
    description: "Buyer fee plus seller fee, completed orders."
    type: sum
    value_format_name: usd_0
    sql: ${TABLE}.net_revenue ;;
  }

  measure: net_revenue_per_listed_ticket {
    type: number
    value_format_name: usd
    sql: 1.0 * ${net_revenue} / NULLIF(${tickets_listed}, 0) ;;
  }
}
