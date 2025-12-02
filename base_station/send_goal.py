#!/usr/bin/env python3
"""
Unified RosGoalSender compatible with the Vendobot UI Delivery Queue.

This file provides BOTH:
 - A class RosGoalSender(robot_ip="x.x.x.x") for the UI
 - A standalone function send_goal(x, y, yaw_deg) for CLI compatibility
"""

import roslibpy
import uuid
import time
import math


# -------------------------------------
# Quaternion Conversion
# -------------------------------------
def yaw_to_quaternion(yaw_deg):
    yaw_rad = math.radians(yaw_deg)
    return {
        'x': 0.0,
        'y': 0.0,
        'z': math.sin(yaw_rad / 2.0),
        'w': math.cos(yaw_rad / 2.0)
    }


# ============================================================
#   MAIN CLASS USED BY main_interface.py
# ============================================================
class RosGoalSender:
    """
    Clean class wrapper so main_interface can call:

        self.goal_sender = RosGoalSender(robot_ip="192.168.2.115")
        self.goal_sender.send_goal(x, y, yaw)

    This class opens a new rosbridge connection per goal,
    which is safe and matches your previous design.
    """

    def __init__(self, robot_ip="192.168.2.115", port=9090):
        self.robot_ip = robot_ip
        self.port = port

    # ----------------------------
    # Send navigation goal
    # ----------------------------
    def send_goal(self, x, y, yaw_deg):
        print("\n===== Sending Goal =====")
        print(f"Robot IP: {self.robot_ip}")
        print(f"Goal: x={x}, y={y}, yaw={yaw_deg}°")

        # Connect to rosbridge
        ros = roslibpy.Ros(host=self.robot_ip, port=self.port)
        ros.run()

        cancel_pub = roslibpy.Topic(ros, '/move_base/cancel', 'actionlib_msgs/GoalID')
        goal_pub   = roslibpy.Topic(ros, '/move_base/goal',   'move_base_msgs/MoveBaseActionGoal')

        # 1. Cancel previous goal
        cancel_pub.publish(roslibpy.Message({'id': ''}))
        time.sleep(0.2)

        # 2. Create goal ID
        goal_id = str(uuid.uuid4())

        # 3. Build quaternion
        quat = yaw_to_quaternion(yaw_deg)

        # 4. Build MoveBaseActionGoal
        goal_msg = {
            'header': {
                'seq': 0,
                'stamp': {'secs': 0, 'nsecs': 0},
                'frame_id': ''
            },
            'goal_id': {
                'stamp': {'secs': 0, 'nsecs': 0},
                'id': goal_id
            },
            'goal': {
                'target_pose': {
                    'header': {'frame_id': 'map'},
                    'pose': {
                        'position': {
                            'x': float(x),
                            'y': float(y),
                            'z': 0.0
                        },
                        'orientation': quat
                    }
                }
            }
        }

        # 5. Publish goal
        print(f"[GoalSender] Sending goal ID: {goal_id}")
        goal_pub.publish(roslibpy.Message(goal_msg))

        # Let message send fully
        time.sleep(0.5)

        goal_pub.unadvertise()
        ros.terminate()
        print("Goal sent.\n")


# ============================================================
#   BACKWARD-COMPATIBLE CLI FUNCTION
# ============================================================
def send_goal(x, y, yaw_deg, robot_ip="192.168.2.115"):
    """
    Legacy function so your old scripts still work.
    """
    sender = RosGoalSender(robot_ip=robot_ip)
    sender.send_goal(x, y, yaw_deg)


# ============================================================
#   COMMAND LINE SUPPORT
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Send goal to robot")
    parser.add_argument("x", type=float, help="X coordinate")
    parser.add_argument("y", type=float, help="Y coordinate")
    parser.add_argument("yaw", type=float, help="Yaw in degrees")
    parser.add_argument("--ip", type=str, default="192.168.2.115", help="Robot IP")

    args = parser.parse_args()
    send_goal(args.x, args.y, args.yaw, robot_ip=args.ip)
