# ================================================================
#  04_scd2_update.py
#  STEP 4 of the pipeline.
#
#  WHAT THIS DOES (SCD TYPE 2 LOGIC):
#  For each table, compare Day2 CSV against the CURRENT row
#  (is_current = 1) in the dim table. If an SCD2 column changed:
#      1. EXPIRE the old row -> is_current = 0,
#                                effective_end_date = change date
#      2. INSERT a brand new row with the new value ->
#                                is_current = 1,
#                                effective_start_date = change date,
#                                effective_end_date = NULL
#
#  This keeps full history — both old and new values exist in
#  the table, just one is marked current and one is not.
#
#  SCD2 columns per table:
#      dim_customer   -> city, loyalty_tier
#      dim_restaurant -> cuisine_type, price_range
#      dim_menu_item  -> category
#      dim_agent      -> vehicle_type, status
# ================================================================

import pandas as pd
import mysql.connector
from db_config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# SCD2 - Customer (city, loyalty_tier)
def scd2_customers(conn):
    print("\nChecking dim_customer...")
    df_new = pd.read_csv(
        "source_data/customers_day2.csv",
        dtype={"customer_id": str, "phone": str}
    )

    cursor = conn.cursor(dictionary=True)
    write_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():

        cursor.execute(
            "SELECT * FROM dim_customer WHERE customer_id=%s AND is_current=1",
            (row["customer_id"],)
        )
        existing = cursor.fetchone()

        if existing is None:
            continue

        if (existing["city"] != row["city"] or
                existing["loyalty_tier"] != row["loyalty_tier"]):

            change_date = str(row["last_updated"])

            write_cursor.execute("""
                UPDATE dim_customer
                SET is_current=0,
                    effective_end_date=%s
                WHERE customer_key=%s
            """, (change_date, existing["customer_key"]))

            write_cursor.execute("""
                INSERT INTO dim_customer
                (
                    customer_id,name,phone,email,city,area,
                    loyalty_tier,platform,
                    effective_start_date,effective_end_date,is_current
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
            """, (
                row["customer_id"],
                row["name"],
                row["phone"],
                row["email"],
                row["city"],
                row["area"],
                row["loyalty_tier"],
                row["platform"],
                change_date
            ))

            changed_count += 1

    conn.commit()
    cursor.close()
    write_cursor.close()

    print(f"SCD2 changes applied: {changed_count}")


# SCD2 - Restaurant (cuisine_type, price_range)
def scd2_restaurants(conn):
    print("\nChecking dim_restaurant...")
    df_new = pd.read_csv(
        "source_data/restaurants_day2.csv",
        dtype={"restaurant_id": str}
    )

    cursor = conn.cursor(dictionary=True)
    write_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():

        cursor.execute(
            "SELECT * FROM dim_restaurant WHERE restaurant_id=%s AND is_current=1",
            (row["restaurant_id"],)
        )
        existing = cursor.fetchone()

        if existing is None:
            continue

        if (existing["cuisine_type"] != row["cuisine_type"] or
                existing["price_range"] != row["price_range"]):

            change_date = str(row["last_updated"])

            write_cursor.execute("""
                UPDATE dim_restaurant
                SET is_current=0,
                    effective_end_date=%s
                WHERE restaurant_key=%s
            """, (change_date, existing["restaurant_key"]))

            write_cursor.execute("""
                INSERT INTO dim_restaurant
                (
                    restaurant_id,name,owner_name,city,area,
                    cuisine_type,avg_rating,price_range,
                    effective_start_date,effective_end_date,is_current
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
            """, (
                row["restaurant_id"],
                row["name"],
                existing["owner_name"],
                row["city"],
                row["area"],
                row["cuisine_type"],
                existing["avg_rating"],
                row["price_range"],
                change_date
            ))

            changed_count += 1

    conn.commit()
    cursor.close()
    write_cursor.close()

    print(f"SCD2 changes applied: {changed_count}")


# SCD2 - Menu Item (category)
def scd2_menu_items(conn):
    print("\nChecking dim_menu_item...")
    df_new = pd.read_csv(
        "source_data/menu_items_day2.csv",
        dtype={"item_id": str, "restaurant_id": str}
    )

    cursor = conn.cursor(dictionary=True)
    write_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():

        cursor.execute(
            "SELECT * FROM dim_menu_item WHERE item_id=%s AND is_current=1",
            (row["item_id"],)
        )
        existing = cursor.fetchone()

        if existing is None:
            continue

        if existing["category"] != row["category"]:

            change_date = str(row["last_updated"])

            write_cursor.execute("""
                UPDATE dim_menu_item
                SET is_current=0,
                    effective_end_date=%s
                WHERE item_key=%s
            """, (change_date, existing["item_key"]))

            is_veg = 1 if row["is_veg"] == "Yes" else 0

            write_cursor.execute("""
                INSERT INTO dim_menu_item
                (
                    item_id,restaurant_id,item_name,category,
                    price,is_veg,
                    effective_start_date,effective_end_date,is_current
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,NULL,1)
            """, (
                row["item_id"],
                row["restaurant_id"],
                row["item_name"],
                row["category"],
                existing["price"],
                is_veg,
                change_date
            ))

            changed_count += 1

    conn.commit()
    cursor.close()
    write_cursor.close()

    print(f"SCD2 changes applied: {changed_count}")


# SCD2 - Agent (vehicle_type, status)
def scd2_agents(conn):
    print("\nChecking dim_agent...")
    df_new = pd.read_csv(
        "source_data/delivery_agents_day2.csv",
        dtype={"agent_id": str, "phone": str}
    )

    cursor = conn.cursor(dictionary=True)
    write_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():

        cursor.execute(
            "SELECT * FROM dim_agent WHERE agent_id=%s AND is_current=1",
            (row["agent_id"],)
        )
        existing = cursor.fetchone()

        if existing is None:
            continue

        if (existing["vehicle_type"] != row["vehicle_type"] or
                existing["status"] != row["status"]):

            change_date = str(row["last_updated"])

            write_cursor.execute("""
                UPDATE dim_agent
                SET is_current=0,
                    effective_end_date=%s
                WHERE agent_key=%s
            """, (change_date, existing["agent_key"]))

            write_cursor.execute("""
                INSERT INTO dim_agent
                (
                    agent_id,name,phone,city,
                    vehicle_type,status,total_deliveries,
                    effective_start_date,effective_end_date,is_current
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
            """, (
                row["agent_id"],
                row["name"],
                existing["phone"],
                row["city"],
                row["vehicle_type"],
                row["status"],
                existing["total_deliveries"],
                change_date
            ))

            changed_count += 1

    conn.commit()
    cursor.close()
    write_cursor.close()

    print(f"SCD2 changes applied: {changed_count}")


def main():

    print("=" * 50)
    print("STEP 4 - SCD TYPE 2 UPDATE")
    print("=" * 50)

    conn = get_connection()

    scd2_customers(conn)
    scd2_restaurants(conn)
    scd2_menu_items(conn)
    scd2_agents(conn)

    conn.close()

    print("\nSCD2 update completed.")
    print("Run 05_incremental_load.py next.")


if __name__ == "__main__":
    main()