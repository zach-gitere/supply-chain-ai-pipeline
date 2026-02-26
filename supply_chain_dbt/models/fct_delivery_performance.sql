{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_orders') }}
)

select
    country,
    city,
    status,
    count(order_id) as total_orders,
    -- We sum the 1s and 0s to get total late count
    sum(late_delivery_risk) as late_orders,
    -- We calculate the % by taking the average of the 1s and 0s
    round(avg(late_delivery_risk) * 100, 2) as late_delivery_rate_pct,
    sum(sales_amount) as total_sales
from orders
group by 1, 2, 3