#!/usr/bin/env python3
import roslibpy
import time

ROBOT_IP = "192.168.2.115"
ROBOT_PORT = 9090

ros = None
cmd_vel_pub = None


def init_connection():
    """Create persistent rosbridge connection."""
    global ros, cmd_vel_pub
    if ros and ros.is_connected:
        return

    print("[ROS] Connecting to rosbridge at {}:{} ...".format(ROBOT_IP, ROBOT_PORT))
    ros = roslibpy.Ros(host=ROBOT_IP, port=ROBOT_PORT)
    ros.run()

    cmd_vel_pub = roslibpy.Topic(
        ros,
        '/cmd_vel',
        'geometry_msgs/Twist'
    )

    print("[ROS] Connected & /cmd_vel publisher ready.")


def send_cmd_vel(lin, ang):
    """Send velocity command."""
    global cmd_vel_pub
    if not cmd_vel_pub:
        init_connection()

    msg = {
        'linear': {'x': lin, 'y': 0.0, 'z': 0.0},
        'angular': {'x': 0.0, 'y': 0.0, 'z': ang}
    }

    cmd_vel_pub.publish(roslibpy.Message(msg))
    print(f"[TELEOP] lin={lin:.2f}, ang={ang:.2f}")


def stop_robot():
    """Send zero velocity."""
    send_cmd_vel(0.0, 0.0)
    print("[TELEOP] STOP")


def close_connection():
    global ros, cmd_vel_pub
    if cmd_vel_pub:
        cmd_vel_pub.unadvertise()
    if ros:
        ros.terminate()
        print("[ROS] Connection closed.")
