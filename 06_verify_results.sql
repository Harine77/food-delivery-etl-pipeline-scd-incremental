-- ================================================================
--  06_verify_results.sql
--  STEP 6 of the pipeline.
-- ================================================================

USE food_delivery_scd;

-- ────────────────────────────────────────────────────────────
-- CHECK 1: SCD1 proof — dim_customer
-- C002, C010, C014 should show their NEW phone/email,
-- and there should be ONLY ONE row each (no history kept)
-- ────────────────────────────────────────────────────────────
SELECT customer_id, name, phone, email, city, loyalty_tier, is_current
FROM dim_customer
WHERE customer_id IN ('C002','C010','C014')
ORDER BY customer_id;
-- Expected: 1 row per customer_id, phone/email = Day2 values


-- ────────────────────────────────────────────────────────────
-- CHECK 2: SCD2 proof — dim_customer
-- C003, C008, C015 should show TWO rows each:
-- one with is_current = 0 (old, expired) and one with is_current = 1 (new)
-- ────────────────────────────────────────────────────────────
SELECT customer_id, name, city, loyalty_tier,
       effective_start_date, effective_end_date, is_current
FROM dim_customer
WHERE customer_id IN ('C003','C008','C015')
ORDER BY customer_id, effective_start_date;
-- Expected: 2 rows per customer_id (history preserved)


-- ────────────────────────────────────────────────────────────
-- CHECK 3: Incremental load proof — new customers
-- C021, C022, C023 should now exist (they didn't in Day1)
-- ────────────────────────────────────────────────────────────
SELECT customer_id, name, city, effective_start_date
FROM dim_customer
WHERE customer_id IN ('C021','C022','C023');
-- Expected: 3 rows


-- ────────────────────────────────────────────────────────────
-- CHECK 4: SCD1 proof — dim_restaurant (rating/owner overwritten)
-- ────────────────────────────────────────────────────────────
SELECT restaurant_id, name, owner_name, avg_rating, is_current
FROM dim_restaurant
WHERE restaurant_id IN ('R001','R007')
ORDER BY restaurant_id;


-- ────────────────────────────────────────────────────────────
-- CHECK 5: SCD2 proof — dim_restaurant (cuisine/price history)
-- ────────────────────────────────────────────────────────────
SELECT restaurant_id, name, cuisine_type, price_range,
       effective_start_date, effective_end_date, is_current
FROM dim_restaurant
WHERE restaurant_id IN ('R005','R014')
ORDER BY restaurant_id, effective_start_date;


-- ────────────────────────────────────────────────────────────
-- CHECK 6: Incremental — new restaurants R016, R017
-- ────────────────────────────────────────────────────────────
SELECT restaurant_id, name, cuisine_type, effective_start_date
FROM dim_restaurant
WHERE restaurant_id IN ('R016','R017');


-- ────────────────────────────────────────────────────────────
-- CHECK 7: SCD1 proof — dim_menu_item (price overwritten)
-- ────────────────────────────────────────────────────────────
SELECT item_id, item_name, price, is_current
FROM dim_menu_item
WHERE item_id IN ('M001','M005','M009','M015')
ORDER BY item_id;


-- ────────────────────────────────────────────────────────────
-- CHECK 8: SCD2 proof — dim_menu_item (category history)
-- ────────────────────────────────────────────────────────────
SELECT item_id, item_name, category,
       effective_start_date, effective_end_date, is_current
FROM dim_menu_item
WHERE item_id IN ('M007','M013')
ORDER BY item_id, effective_start_date;


-- ────────────────────────────────────────────────────────────
-- CHECK 9: SCD1 proof — dim_agent (phone/deliveries overwritten)
-- ────────────────────────────────────────────────────────────
SELECT agent_id, name, phone, total_deliveries, is_current
FROM dim_agent
WHERE agent_id IN ('A001','A003','A007')
ORDER BY agent_id;


-- ────────────────────────────────────────────────────────────
-- CHECK 10: SCD2 proof — dim_agent (vehicle/status history)
-- ────────────────────────────────────────────────────────────
SELECT agent_id, name, vehicle_type, status,
       effective_start_date, effective_end_date, is_current
FROM dim_agent
WHERE agent_id IN ('A005','A008')
ORDER BY agent_id, effective_start_date;


-- ────────────────────────────────────────────────────────────
-- CHECK 11: Incremental — new orders ORD021 to ORD027
-- ────────────────────────────────────────────────────────────
SELECT order_id, customer_id, restaurant_id, order_date, amount, loaded_at
FROM fact_orders
WHERE order_id IN ('ORD021','ORD022','ORD023','ORD024','ORD025','ORD026','ORD027')
ORDER BY order_id;
-- Expected: 7 rows (these did not exist after Day1 load)


-- ────────────────────────────────────────────────────────────
-- CHECK 12: Overall row counts — quick sanity check
-- ────────────────────────────────────────────────────────────
SELECT 'dim_customer'   AS table_name, COUNT(*) AS total_rows,
       SUM(is_current)  AS current_rows FROM dim_customer
UNION ALL
SELECT 'dim_restaurant', COUNT(*), SUM(is_current) FROM dim_restaurant
UNION ALL
SELECT 'dim_menu_item',  COUNT(*), SUM(is_current) FROM dim_menu_item
UNION ALL
SELECT 'dim_agent',      COUNT(*), SUM(is_current) FROM dim_agent
UNION ALL
SELECT 'fact_orders',    COUNT(*), NULL FROM fact_orders;

-- Expected totals after everything runs:
--   dim_customer   : 26 total rows (20 day1 + 3 scd2-versioned + 3 new)   | 23 current
--   dim_restaurant : 19 total rows (15 day1 + 2 scd2-versioned + 2 new)   | 17 current
--   dim_menu_item   : 19 total rows (15 day1 + 2 scd2-versioned + 2 new)  | 17 current
--   dim_agent       : 16 total rows (12 day1 + 2 scd2-versioned + 2 new) | 14 current
--   fact_orders     : 27 total rows (20 day1 + 7 day2)


-- ────────────────────────────────────────────────────────────
-- CHECK 13: ETL control table — proves incremental tracking works
-- ────────────────────────────────────────────────────────────
SELECT * FROM etl_control;
-- Expected: orders -> last_loaded_date = 2024-02-27 (max date from day2)