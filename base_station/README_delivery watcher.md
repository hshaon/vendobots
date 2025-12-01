# Delivery Watcher -- PostgreSQL → ROS Goal Sender

*A real-time system that listens for database inserts and dispatches ROS
navigation goals.*

This README is based on the latest implementation of
`delivery_watcher.py` (see project files) and is formatted GitHub‑style
for direct use in your repository.

------------------------------------------------------------------------

## Overview

The **Delivery Watcher** monitors PostgreSQL for **INSERT events** on
the `delivery_records` table.\
When a new delivery request is inserted, the watcher:

1.  Receives a `NOTIFY` event\
2.  Extracts the delivery ID\
3.  Fetches destination coordinates from the DB\
4.  Sends a navigation goal to the robot using `send_goal.py`\
5.  Logs each step for visibility

This creates an automated, database‑driven delivery dispatch pipeline.

------------------------------------------------------------------------

## Architecture

    ┌──────────────────┐
    │ User / Backend    │
    │ inserts delivery  │
    └─────────┬────────┘
              │ INSERT
              ▼
    ┌──────────────────────────┐
    │ PostgreSQL               │
    │ delivery_records table   │
    │ TRIGGER → NOTIFY         │
    └─────────┬────────────────┘
              │ LISTEN
              ▼
    ┌──────────────────────────┐
    │ delivery_watcher.py      │
    │ Parses payload           │
    │ Fetches coordinates      │
    │ Calls send_goal()        │
    └─────────┬────────────────┘
              │ /move_base_simple/goal
              ▼
    ┌──────────────────────────┐
    │ ROS Robot (rosbridge)    │
    │ Navigates to target      │
    └──────────────────────────┘

------------------------------------------------------------------------

## Files

### `delivery_watcher.py`

Main listener script → listens to PostgreSQL notifications and sends ROS
navigation goals.

### `send_goal.py`

Helper script that connects to rosbridge and publishes `PoseStamped`
goals.

------------------------------------------------------------------------

## Requirements

Install dependencies:

``` bash
pip install psycopg2-binary roslibpy
```

PostgreSQL must support `NOTIFY/LISTEN`.

------------------------------------------------------------------------

## PostgreSQL Trigger Setup (NOTIFY on INSERT)

### 1. Create NOTIFY trigger function

``` sql
CREATE OR REPLACE FUNCTION notify_new_delivery()
RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify(
        'delivery_records_channel',
        row_to_json(NEW)::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 2. Attach trigger to `delivery_records`

``` sql
CREATE TRIGGER delivery_insert_trigger
AFTER INSERT ON delivery_records
FOR EACH ROW
EXECUTE FUNCTION notify_new_delivery();
```

Now every new delivery triggers a JSON payload to the watcher.

------------------------------------------------------------------------

## Running the Delivery Watcher

Run:

``` bash
python3 delivery_watcher.py
```

Example output:

    Starting PostgreSQL delivery watcher...
    Listening on channel: delivery_records_channel ...

    New delivery notify received!
    Raw payload: {"id": 7, "robot_id": 1}
    Delivery ID = 7
    New Goal -> X=1.0000, Y=2.0000, Yaw=0
    Goal sent for delivery 7

------------------------------------------------------------------------

## How INSERT Alerts Work

`NOTIFY` sends an event from PostgreSQL → `LISTEN` receives it in
Python.

Python waits efficiently using:

``` python
select.select([conn], [], [], 5)
```

When notifications arrive:

``` python
conn.poll()
notify = conn.notifies.pop(0)
```

This contains the JSON from the trigger (`row_to_json(NEW)`).

------------------------------------------------------------------------

## How ROS Goal Sending Works

The watcher calls:

``` python
send_goal(x, y, yaw)
```

`send_goal.py`:

-   Connects to `rosbridge_server`\
-   Publishes `/move_base_simple/goal`\
-   Formats a correct `geometry_msgs/PoseStamped`\
-   Uses quaternion for yaw orientation\
-   Prints result

If rosbridge is offline, errors are logged cleanly.

------------------------------------------------------------------------

## Test INSERT & Trigger

Insert into table:

``` sql
INSERT INTO delivery_records (robot_id, dest_pos_x, dest_pos_y)
VALUES (1, 1.25, 2.75);
```

Expected watcher output:

    New delivery notify received!
    Delivery ID = 12
    New Goal -> X=1.2500, Y=2.7500, Yaw=0
    Goal sent for delivery 12

Robot should start moving immediately.

------------------------------------------------------------------------

## Troubleshooting

### No notifications?

-   Check trigger exists:

    ``` sql
    \d delivery_records
    ```

-   Restart PostgreSQL

-   Ensure channel name matches: `delivery_records_channel`

### Decimal conversion error?

Latest watcher properly converts:

``` python
float(Decimal)
```

### Robot not moving?

-   Check rosbridge:

        roslaunch rosbridge_server rosbridge_websocket.launch

-   Test network:

        ping ROBOT_IP

------------------------------------------------------------------------

## License

MIT License

------------------------------------------------------------------------

## Support

Open an Issue or Pull Request for improvements.
