# ================================================================
#
#  WHAT THIS DOES:
#  Loads all 5 Day1 CSVs into the dimension and fact tables for
#  the FIRST TIME. Every dimension row gets:
#      effective_start_date = the date in the CSV
#      effective_end_date   = NULL   (still open / current)
#      is_current            = 1
#
#  This is the "Day 0" baseline. Day 2 scripts will compare
#  against this data to detect SCD1 / SCD2 / new changes.
# ================================================================
import pandas as pd
import mysql.connector
from db_config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# Load Customer Dimension
def load_customers(conn):
    df = pd.read_csv("source_data/customers_day1.csv")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_customer
            (customer_id, name, phone, email, city, area,
             loyalty_tier, platform, effective_start_date,
             effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["customer_id"],
            row["name"],
            row["phone"],
            row["email"],
            row["city"],
            row["area"],
            row["loyalty_tier"],
            row["platform"],
            row["last_updated"]
        ))

    conn.commit()
    cursor.close()
    print(f"Inserted {len(df)} customers")


# Load Restaurant Dimension
def load_restaurants(conn):
    df = pd.read_csv("source_data/restaurants_day1.csv")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_restaurant
            (restaurant_id, name, owner_name, city, area,
             cuisine_type, avg_rating, price_range,
             effective_start_date, effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["restaurant_id"],
            row["name"],
            row["owner_name"],
            row["city"],
            row["area"],
            row["cuisine_type"],
            row["avg_rating"],
            row["price_range"],
            row["last_updated"]
        ))

    conn.commit()
    cursor.close()
    print(f"Inserted {len(df)} restaurants")


# Load Menu Item Dimension
def load_menu_items(conn):
    df = pd.read_csv("source_data/menu_items_day1.csv")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        is_veg = 1 if row["is_veg"] == "Yes" else 0

        cursor.execute("""
            INSERT INTO dim_menu_item
            (item_id, restaurant_id, item_name, category,
             price, is_veg, effective_start_date,
             effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["item_id"],
            row["restaurant_id"],
            row["item_name"],
            row["category"],
            row["price"],
            is_veg,
            row["last_updated"]
        ))

    conn.commit()
    cursor.close()
    print(f"Inserted {len(df)} menu items")


# Load Agent Dimension
def load_agents(conn):
    df = pd.read_csv("source_data/delivery_agents_day1.csv")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO dim_agent
            (agent_id, name, phone, city, vehicle_type,
             status, total_deliveries, effective_start_date,
             effective_end_date, is_current)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULL,1)
        """, (
            row["agent_id"],
            row["name"],
            row["phone"],
            row["city"],
            row["vehicle_type"],
            row["status"],
            int(row["total_deliveries"]),
            row["last_updated"]
        ))

    conn.commit()
    cursor.close()
    print(f"Inserted {len(df)} agents")


# Load Orders Fact Table
def load_orders(conn):
    df = pd.read_csv("source_data/orders_day1.csv")
    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO fact_orders
            (order_id, customer_id, restaurant_id, item_id,
             order_date, amount, payment_mode,
             delivery_status, agent_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            row["order_id"],
            row["customer_id"],
            row["restaurant_id"],
            row["item_id"],
            row["order_date"],
            row["amount"],
            row["payment_mode"],
            row["delivery_status"],
            row["agent_id"]
        ))

    conn.commit()
    print(f"Inserted {len(df)} orders")

    # Update control table
    max_date = df["order_date"].max()

    cursor.execute("""
        INSERT INTO etl_control (source_name, last_loaded_date)
        VALUES ('orders', %s)
        ON DUPLICATE KEY UPDATE
        last_loaded_date = %s
    """, (max_date, max_date))

    conn.commit()
    cursor.close()

    print(f"Control table updated: {max_date}")


def main():
    conn = get_connection()

    print("Connected to MySQL")

    load_customers(conn)
    load_restaurants(conn)
    load_menu_items(conn)
    load_agents(conn)
    load_orders(conn)

    conn.close()

    print("Day 1 Initial Load Completed")


if __name__ == "__main__":
    main()