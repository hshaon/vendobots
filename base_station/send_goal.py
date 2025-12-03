#!/usr/bin/env python3
"""
RosGoalSender compatible with Vendobot UI.

Supports two modes:
 - UI mode: reuse an existing roslibpy.Ros connection (no extra threads, no Twisted conflicts)
 - CLI mode: create its own Ros connection, send a goal, and exit
"""

import math
import time
import uuid

import roslibpy


def yaw_to_quaternion(yaw_deg: float):
    """Convert yaw in degrees to a simple quaternion around Z."""
    yaw_rad = math.radians(yaw_deg)
    return {
        'x': 0.0,
        'y': 0.0,
        'z': math.sin(yaw_rad / 2.0),
        'w': math.cos(yaw_rad / 2.0),
    }


class RosGoalSender:
    """
    Main class used by the Qt UI.

    In the UI, you should construct it with an existing roslibpy.Ros:

        sender = RosGoalSender(ros=telemetry.ros)

    That way, there is only ONE rosbridge connection in the app,
    and we avoid Twisted / threading conflicts.
    """

    def __init__(self, ros: roslibpy.Ros = None, robot_ip: str = "192.168.2.115", port: int = 9090):
        """
        If `ros` is provided, reuse that connection.
        If not, create our own connection (CLI usage).
        """
        if ros is not None:
            # Shared connection (UI mode)
            self.ros = ros
            self._owns_connection = False
        else:
            # Standalone connection (CLI mode)
            self.ros = roslibpy.Ros(host=robot_ip, port=port)
            self._owns_connection = True
            print(f"[RosGoalSender] Connecting to rosbridge at {robot_ip}:{port} ...")
            self.ros.run(run_in_thread=True)

    def ensure_connected(self):
        """Ensure rosbridge is connected; only tries to reconnect if we own it."""
        if self.ros.is_connected:
            return

        if not self._owns_connection:
            print("[RosGoalSender] Shared ROS connection is not connected; cannot send goal.")
            return

        print("[RosGoalSender] Reconnecting rosbridge...")
        self.ros.run(run_in_thread=True)

    def send_goal(self, x: float, y: float, yaw_deg: float):
        """Send a MoveBaseActionGoal to /move_base/goal using the existing rosbridge client."""
        print("\n===== Sending Goal =====")
        print(f"Goal: x={x}, y={y}, yaw={yaw_deg}°")

        self.ensure_connected()
        if not self.ros.is_connected:
            print("[RosGoalSender] ERROR: rosbridge is not connected; aborting goal.")
            return

        # 1. Cancel previous goal
        cancel_pub = roslibpy.Topic(self.ros, '/move_base/cancel', 'actionlib_msgs/GoalID')
        cancel_pub.advertise()
        cancel_msg = {'id': ''}
        cancel_pub.publish(roslibpy.Message(cancel_msg))
        time.sleep(0.1)
        cancel_pub.unadvertise()

        # 2. Build quaternion
        quat = yaw_to_quaternion(yaw_deg)

        # 3. Build goal ID
        goal_id = str(uuid.uuid4())

        # 4. Build MoveBaseActionGoal message
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
        goal_pub = roslibpy.Topic(self.ros, '/move_base/goal', 'move_base_msgs/MoveBaseActionGoal')
        goal_pub.advertise()
        print(f"[RosGoalSender] Publishing goal ID: {goal_id}")
        goal_pub.publish(roslibpy.Message(goal_msg))
        time.sleep(0.1)
        goal_pub.unadvertise()

        print("[RosGoalSender] Goal sent.\n")

    def close(self):
        """Close rosbridge only if this instance owns the connection (CLI mode)."""
        if self._owns_connection and self.ros is not None:
            print("[RosGoalSender] Terminating rosbridge connection...")
            self.ros.terminate()


# Backward-compatible CLI usage
def send_goal(x, y, yaw_deg, robot_ip="192.168.2.115", port=9090):
    """
    Legacy helper for CLI:

        python3 send_goal.py 1.0 2.5 0

    This uses its own connection, independent of the Qt UI.
    """
    sender = RosGoalSender(ros=None, robot_ip=robot_ip, port=port)
    sender.send_goal(x, y, yaw_deg)
    time.sleep(0.5)
    sender.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send a navigation goal via rosbridge.")
    parser.add_argument("x", type=float, help="X coordinate in map frame")
    parser.add_argument("y", type=float, help="Y coordinate in map frame")
    parser.add_argument("yaw", type=float, help="Yaw in degrees")
    parser.add_argument("--ip", type=str, default="192.168.2.115", help="Robot rosbridge IP")
    parser.add_argument("--port", type=int, default=9090, help="Robot rosbridge port")

    args = parser.parse_args()
    send_goal(args.x, args.y, args.yaw, robot_ip=args.ip, port=args.port)
