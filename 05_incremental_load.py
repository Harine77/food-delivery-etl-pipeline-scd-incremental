# ================================================================
#  05_incremental_load.py
#  STEP 5 of the pipeline.
#
#  WHAT THIS DOES (INCREMENTAL LOAD LOGIC):
#  Incremental load = only bring in records that are NEW since
#  the last run. Two different patterns are shown here:
#
#  PATTERN A — Dimensions (customers, restaurants, menu_items, agents)
#      Day2 file = FULL snapshot. We already handled "changed"
#      rows in SCD1/SCD2 scripts. This script handles rows that
#      did not exist at all in Day1 -> brand new dimension members.
#
#  PATTERN B — Fact table (orders)
#      Day2 file = ONLY new orders (true incremental extract).
#      We use the etl_control table to know we haven't loaded
#      these yet, then insert all of them. No comparison needed
#      because the source itself only sent new rows.
# ================================================================

import pandas as pd
import mysql.connector
from db_config import DB_CONFIG


SOURCE_PATH = "SOURCE_DATA/"


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ────────────────────────────────────────────────────────────────
# CUSTOMERS (DIM - NEW INSERTS ONLY)
# ────────────────────────────────────────────────────────────────
def incremental_customers(conn):
    print("\n  Checking NEW customers...")

    df = pd.read_csv(SOURCE_PATH + "customers_day2.csv",
                     dtype={"customer_id": str, "phone": str})

    existing = pd.read_sql("SELECT customer_id FROM dim_customer", conn)
    existing_set = set(existing["customer_id"])

    new_rows = df[~df["customer_id"].isin(existing_set)]

    if new_rows.empty:
        print("    No new customers found.")
        return

    cursor = conn.cursor()

    for _, row in new_rows.iterrows():
        cursor.execute("""
            INSERT INTO dim_customer
            (customer_id, name, phone, email, city, area,
             loyalty_tier, platform, effective_start_date,
             effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["customer_id"], row["name"], row["phone"], row["email"],
            row["city"], row["area"], row["loyalty_tier"], row["platform"],
            row["last_updated"]
        ))

    conn.commit()
    cursor.close()

    print(f"    Inserted {len(new_rows)} new customers")


# ────────────────────────────────────────────────────────────────
# RESTAURANTS
# ────────────────────────────────────────────────────────────────
def incremental_restaurants(conn):
    print("\n  Checking NEW restaurants...")

    df = pd.read_csv(SOURCE_PATH + "restaurants_day2.csv",
                     dtype={"restaurant_id": str})

    existing = pd.read_sql("SELECT restaurant_id FROM dim_restaurant", conn)
    existing_set = set(existing["restaurant_id"])

    new_rows = df[~df["restaurant_id"].isin(existing_set)]

    if new_rows.empty:
        print("    No new restaurants found.")
        return

    cursor = conn.cursor()

    for _, row in new_rows.iterrows():
        cursor.execute("""
            INSERT INTO dim_restaurant
            (restaurant_id, name, owner_name, city, area,
             cuisine_type, avg_rating, price_range,
             effective_start_date, effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["restaurant_id"], row["name"], row["owner_name"],
            row["city"], row["area"], row["cuisine_type"],
            row["avg_rating"], row["price_range"], row["last_updated"]
        ))

    conn.commit()
    cursor.close()

    print(f"    Inserted {len(new_rows)} new restaurants")


# ────────────────────────────────────────────────────────────────
# MENU ITEMS
# ────────────────────────────────────────────────────────────────
def incremental_menu_items(conn):
    print("\n  Checking NEW menu items...")

    df = pd.read_csv(SOURCE_PATH + "menu_items_day2.csv",
                     dtype={"item_id": str, "restaurant_id": str})

    existing = pd.read_sql("SELECT item_id FROM dim_menu_item", conn)
    existing_set = set(existing["item_id"])

    new_rows = df[~df["item_id"].isin(existing_set)]

    if new_rows.empty:
        print("    No new menu items found.")
        return

    cursor = conn.cursor()

    for _, row in new_rows.iterrows():
        is_veg = 1 if str(row["is_veg"]).lower() == "yes" else 0

        cursor.execute("""
            INSERT INTO dim_menu_item
            (item_id, restaurant_id, item_name, category, price,
             is_veg, effective_start_date, effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["item_id"], row["restaurant_id"], row["item_name"],
            row["category"], row["price"], is_veg, row["last_updated"]
        ))

    conn.commit()
    cursor.close()

    print(f"    Inserted {len(new_rows)} new menu items")


# ────────────────────────────────────────────────────────────────
# AGENTS
# ────────────────────────────────────────────────────────────────
def incremental_agents(conn):
    print("\n  Checking NEW agents...")

    df = pd.read_csv(SOURCE_PATH + "delivery_agents_day2.csv",
                     dtype={"agent_id": str, "phone": str})

    existing = pd.read_sql("SELECT agent_id FROM dim_agent", conn)
    existing_set = set(existing["agent_id"])

    new_rows = df[~df["agent_id"].isin(existing_set)]

    if new_rows.empty:
        print("    No new agents found.")
        return

    cursor = conn.cursor()

    for _, row in new_rows.iterrows():
        cursor.execute("""
            INSERT INTO dim_agent
            (agent_id, name, phone, city, vehicle_type, status,
             total_deliveries, effective_start_date, effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["agent_id"], row["name"], row["phone"], row["city"],
            row["vehicle_type"], row["status"], int(row["total_deliveries"]),
            row["last_updated"]
        ))

    conn.commit()
    cursor.close()

    print(f"    Inserted {len(new_rows)} new agents")


# ────────────────────────────────────────────────────────────────
# ORDERS (FACT - TRUE INCREMENTAL)
# ────────────────────────────────────────────────────────────────
def incremental_orders(conn):
    print("\n  Loading NEW orders...")

    control = pd.read_sql("""
        SELECT last_loaded_date
        FROM etl_control
        WHERE source_name = 'orders'
    """, conn)

    last_loaded_date = control["last_loaded_date"].iloc[0] if not control.empty else None
    print(f"    Last loaded date: {last_loaded_date}")

    df = pd.read_csv(SOURCE_PATH + "orders_day2.csv",
                     dtype={"order_id": str, "customer_id": str,
                            "restaurant_id": str, "item_id": str,
                            "agent_id": str})

    df["order_date"] = pd.to_datetime(df["order_date"])

    existing = pd.read_sql("SELECT order_id FROM fact_orders", conn)
    existing_set = set(existing["order_id"])

    new_rows = df[~df["order_id"].isin(existing_set)]

    if new_rows.empty:
        print("    No new orders found.")
        return

    cursor = conn.cursor()

    for _, row in new_rows.iterrows():
        cursor.execute("""
            INSERT INTO fact_orders
            (order_id, customer_id, restaurant_id, item_id, order_date,
             amount, payment_mode, delivery_status, agent_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row["order_id"], row["customer_id"], row["restaurant_id"],
            row["item_id"], row["order_date"].date(), row["amount"],
            row["payment_mode"], row["delivery_status"], row["agent_id"]
        ))

    conn.commit()

    # update control table
    new_max_date = new_rows["order_date"].max().date()

    cursor.execute("""
        UPDATE etl_control
        SET last_loaded_date = %s
        WHERE source_name = 'orders'
    """, (new_max_date,))

    conn.commit()
    cursor.close()

    print(f"    Inserted {len(new_rows)} new orders")
    print(f"    Updated control table to {new_max_date}")


# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(" STEP 5 — INCREMENTAL LOAD PIPELINE")
    print("=" * 60)

    conn = get_connection()
    print(" Connected to MySQL")

    incremental_customers(conn)
    incremental_restaurants(conn)
    incremental_menu_items(conn)
    incremental_agents(conn)
    incremental_orders(conn)

    conn.close()

    print("\n" + "=" * 60)
    print(" STEP 5 COMPLETE")
    print(" Run STEP 6 verification script next")
    print("=" * 60)


if __name__ == "__main__":
    main()