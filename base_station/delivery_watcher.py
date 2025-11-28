#!/usr/bin/env python3
import psycopg2
import select
import json
from decimal import Decimal
from send_goal import send_goal  # import fixed-IP goal sender


# -----------------------------
# DB Configuration
# -----------------------------
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "vendor_bot",
    "user": "postgres",
    "password": "102403"
}


# -----------------------------
# Start Watching for new orders
# -----------------------------
def start_watcher():
    print("Starting PostgreSQL delivery watcher...")

    # Connect to PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    cur = conn.cursor()
    cur.execute("LISTEN delivery_records_channel;")

    print("Listening on channel: delivery_records_channel ...")

    while True:
        # Wait for NOTIFY events
        if select.select([conn], [], [], 5) == ([], [], []):
            continue

        conn.poll()

        while conn.notifies:
            notify = conn.notifies.pop(0)
            print("\nNew delivery notify received!")
            print("Raw payload:", notify.payload)

            # Parse JSON payload from trigger
            try:
                data = json.loads(notify.payload)
            except:
                print("Invalid JSON payload.")
                continue

            delivery_id = data.get("id")
            if not delivery_id:
                print("No delivery ID in payload.")
                continue

            print(f"Delivery ID = {delivery_id}")

            # Fetch coordinates from DB
            cur2 = conn.cursor()
            cur2.execute("""
                SELECT dest_pos_x, dest_pos_y
                FROM delivery_records
                WHERE id=%s
            """, (delivery_id,))
            row = cur2.fetchone()
            cur2.close()

            if not row:
                print("Delivery record not found.")
                continue

            # Convert Decimal to float
            try:
                x = float(row[0]) if isinstance(row[0], Decimal) else row[0]
                y = float(row[1]) if isinstance(row[1], Decimal) else row[1]
            except Exception as e:
                print("Error converting DB values:", e)
                continue

            yaw = 0  # Default yaw (modify if you add yaw column)

            print(f"New Goal -> X={x:.4f}, Y={y:.4f}, Yaw={yaw}")

            # Send goal to robot
            try:
                send_goal(x, y, yaw)
            except Exception as e:
                print("Error sending goal to robot:", e)
                continue

            print(f"Goal sent for delivery {delivery_id}")
            print("-----------------------------------")


if __name__ == "__main__":
    start_watcher()

