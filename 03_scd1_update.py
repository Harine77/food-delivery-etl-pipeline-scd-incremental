#  WHAT THIS DOES (SCD TYPE 1 LOGIC):
#  For each table, compare Day2 CSV against what's currently in
#  the dim table. If an SCD1 column changed (phone, email, price,
#  avg_rating, owner_name, total_deliveries) -> OVERWRITE the
#  existing row directly. No new row, no history kept.

import pandas as pd
import mysql.connector
from db_config import DB_CONFIG

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# Customer SCD1 (phone, email)
def scd1_customers(conn):
    print("\nChecking dim_customer for SCD1 changes...")
    df_new = pd.read_csv(
        "source_data/customers_day2.csv",
        dtype={"customer_id": str, "phone": str}
    )

    cursor = conn.cursor(dictionary=True)
    update_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():
        cursor.execute(
            "SELECT * FROM dim_customer WHERE customer_id=%s AND is_current=1",
            (row["customer_id"],)
        )

        existing = cursor.fetchone()

        if existing is None:
            continue

        if existing["phone"] != row["phone"] or existing["email"] != row["email"]:
            update_cursor.execute("""
                UPDATE dim_customer
                SET phone=%s, email=%s
                WHERE customer_key=%s
            """, (
                row["phone"],
                row["email"],
                existing["customer_key"]
            ))
            changed_count += 1

    conn.commit()
    cursor.close()
    update_cursor.close()

    print(f"Customer SCD1 updates: {changed_count}")


# Restaurant SCD1 (avg_rating, owner_name)
def scd1_restaurants(conn):
    print("\nChecking dim_restaurant for SCD1 changes...")
    df_new = pd.read_csv(
        "source_data/restaurants_day2.csv",
        dtype={"restaurant_id": str}
    )

    cursor = conn.cursor(dictionary=True)
    update_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():
        cursor.execute(
            "SELECT * FROM dim_restaurant WHERE restaurant_id=%s AND is_current=1",
            (row["restaurant_id"],)
        )

        existing = cursor.fetchone()

        if existing is None:
            continue

        old_rating = float(existing["avg_rating"])
        new_rating = float(row["avg_rating"])

        if old_rating != new_rating or existing["owner_name"] != row["owner_name"]:
            update_cursor.execute("""
                UPDATE dim_restaurant
                SET avg_rating=%s,
                    owner_name=%s
                WHERE restaurant_key=%s
            """, (
                new_rating,
                row["owner_name"],
                existing["restaurant_key"]
            ))
            changed_count += 1

    conn.commit()
    cursor.close()
    update_cursor.close()

    print(f"Restaurant SCD1 updates: {changed_count}")


# Menu Item SCD1 (price)
def scd1_menu_items(conn):
    print("\nChecking dim_menu_item for SCD1 changes...")
    df_new = pd.read_csv(
        "source_data/menu_items_day2.csv",
        dtype={"item_id": str, "restaurant_id": str}
    )

    cursor = conn.cursor(dictionary=True)
    update_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():
        cursor.execute(
            "SELECT * FROM dim_menu_item WHERE item_id=%s AND is_current=1",
            (row["item_id"],)
        )

        existing = cursor.fetchone()

        if existing is None:
            continue

        old_price = float(existing["price"])
        new_price = float(row["price"])

        if old_price != new_price:
            update_cursor.execute("""
                UPDATE dim_menu_item
                SET price=%s
                WHERE item_key=%s
            """, (
                new_price,
                existing["item_key"]
            ))
            changed_count += 1

    conn.commit()
    cursor.close()
    update_cursor.close()

    print(f"Menu Item SCD1 updates: {changed_count}")


# Agent SCD1 (phone, total_deliveries)
def scd1_agents(conn):
    print("\nChecking dim_agent for SCD1 changes...")
    df_new = pd.read_csv(
        "source_data/delivery_agents_day2.csv",
        dtype={"agent_id": str, "phone": str}
    )

    cursor = conn.cursor(dictionary=True)
    update_cursor = conn.cursor()

    changed_count = 0

    for _, row in df_new.iterrows():
        cursor.execute(
            "SELECT * FROM dim_agent WHERE agent_id=%s AND is_current=1",
            (row["agent_id"],)
        )

        existing = cursor.fetchone()

        if existing is None:
            continue

        if (
            existing["phone"] != row["phone"]
            or existing["total_deliveries"] != int(row["total_deliveries"])
        ):
            update_cursor.execute("""
                UPDATE dim_agent
                SET phone=%s,
                    total_deliveries=%s
                WHERE agent_key=%s
            """, (
                row["phone"],
                int(row["total_deliveries"]),
                existing["agent_key"]
            ))
            changed_count += 1

    conn.commit()
    cursor.close()
    update_cursor.close()

    print(f"Agent SCD1 updates: {changed_count}")


def main():
    print("=" * 50)
    print("STEP 3 - SCD TYPE 1 UPDATE")
    print("=" * 50)

    conn = get_connection()

    scd1_customers(conn)
    scd1_restaurants(conn)
    scd1_menu_items(conn)
    scd1_agents(conn)

    conn.close()

    print("\nSCD1 Update Completed")


if __name__ == "__main__":
    main()