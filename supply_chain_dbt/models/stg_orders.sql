{{ config(materialized='view') }}

with raw_data as (
    select * from {{ source('snowflake_raw', 'RAW_SUPPLY_CHAIN_DATA') }}
)

select
    CAST(ORDER_ITEM_ID AS INT) as order_item_id,
    CAST(ORDER_ID AS INT) as order_id,
    -- Our "Fix the Shift" mappings from earlier
    PROD_CATEGORY_ID as status,        
    ORDER_STATUS as region,           
    PROD_CARD_ID as state,            
    -- THE MISSING PIECE:
    CAST(LATE_DELIVERY_RISK AS INT) as late_delivery_risk, 
    
    CAST(SALES AS FLOAT) as sales_amount,
    ORDER_CITY as city,
    ORDER_COUNTRY as country,
    TO_TIMESTAMP(ORDER_DATE, 'mm/dd/yyyy hh24:mi') as order_timestamp
from raw_data