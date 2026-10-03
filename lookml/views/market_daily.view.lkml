view: market_daily {
  sql_table_name: main.fct_market_daily ;;

  dimension: pk {
    primary_key: yes
    hidden: yes
    sql: ${TABLE}.activity_date || ${TABLE}.market_id || ${TABLE}.category_group || ${TABLE}.day_type ;;
  }

  dimension_group: activity {
    type: time
    timeframes: [date, week, month]
    datatype: date
    sql: ${TABLE}.activity_date ;;
  }

  dimension: market_name { sql: ${TABLE}.market_name ;; }
  dimension: category_group { sql: ${TABLE}.category_group ;; }
  dimension: day_type { sql: ${TABLE}.day_type ;; }

  dimension: is_fee_pilot_market {
    type: yesno
    sql: ${TABLE}.is_fee_pilot_market ;;
  }

  measure: sessions {
    type: sum
    sql: ${TABLE}.sessions ;;
  }

  measure: checkout_starts {
    type: sum
    sql: ${TABLE}.checkout_starts ;;
  }

  measure: orders {
    type: sum
    sql: ${TABLE}.orders ;;
  }

  measure: checkout_to_order_rate {
    type: number
    value_format_name: percent_1
    sql: 1.0 * ${orders} / NULLIF(${checkout_starts}, 0) ;;
  }

  measure: gmv {
    label: "GMV"
    type: sum
    value_format_name: usd_0
    sql: ${TABLE}.gmv ;;
  }

  measure: net_revenue {
    type: sum
    value_format_name: usd_0
    sql: ${TABLE}.net_revenue ;;
  }
}
