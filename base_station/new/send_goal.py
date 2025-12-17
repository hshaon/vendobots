#!/usr/bin/env python3
import roslibpy
import uuid
import time
import math
import argparse

# ----------------------------
# FIXED ROBOT IP ADDRESS
# ----------------------------
ROBOT_IP = "192.168.2.115"  


# ----------------------------
# Convert yaw deg → quaternion
# ----------------------------
def yaw_to_quaternion(yaw_deg):
    yaw_rad = math.radians(yaw_deg)
    return {
        'x': 0.0,
        'y': 0.0,
        'z': math.sin(yaw_rad / 2.0),
        'w': math.cos(yaw_rad / 2.0)
    }


# ----------------------------
# Send navigation goal to robo
# ----------------------------
def send_goal(x, y, yaw_deg):
    print(f"\n===== Sending Goal =====")
    print(f"Robot IP: {ROBOT_IP}")
    print(f"Goal: x={x}, y={y}, yaw={yaw_deg}°")

    # Connect to rosbridge
    ros = roslibpy.Ros(host=ROBOT_IP, port=9090)
    ros.run()

    cancel_pub = roslibpy.Topic(ros, '/move_base/cancel', 'actionlib_msgs/GoalID')
    goal_pub   = roslibpy.Topic(ros, '/move_base/goal',   'move_base_msgs/MoveBaseActionGoal')

    # 1. Cancel previous goal
    cancel_pub.publish(roslibpy.Message({'id': ''}))
    time.sleep(0.2)

    # 2. Unique goal ID
    goal_id = str(uuid.uuid4())

    # 3. Build quaternion
    quat = yaw_to_quaternion(yaw_deg)

    # 4. Build MoveBaseActionGoal
    goal_msg = {
        'header': {
            'seq': 0,
            'stamp': {'secs': 0, 'nsecs': 0},
            'frame_id': 'map'
        },
        'goal_id': {
            'stamp': {'secs': 0, 'nsecs': 0},
            'id': goal_id
        },
        'goal': {
            'target_pose': {
                'header': {'frame_id': 'map'},
                'pose': {
                    'position': {'x': x, 'y': y, 'z': 0},
                    'orientation': quat
                }
            }
        }
    }

    # 5. Publish
    print(f"Sending goal ID: {goal_id}")
    goal_pub.publish(roslibpy.Message(goal_msg))

    # Let message fully send
    time.sleep(0.5)

    goal_pub.unadvertise()
    ros.terminate()
    print("Goal sent.\n")


# ----------------------------
# CLI Support
# Only x y yaw are needed
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send goal to robot with fixed IP.")
    parser.add_argument("x", type=float, help="X coordinate")
    parser.add_argument("y", type=float, help="Y coordinate")
    parser.add_argument("yaw", type=float, help="Yaw in degrees")

    args = parser.parse_args()

    send_goal(args.x, args.y, args.yaw)
