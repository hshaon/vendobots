#!/usr/bin/env python3
import math
import threading
import roslibpy

ROBOT_IP = "192.168.2.115"
ROBOT_PORT = 9090
class Telemetry:
    def __init__(self):
        self._map_lock = threading.Lock()
        self._map_info = None
        self._map_data = None
        self._map_ready = False

        self._pose_lock = threading.Lock()
        self._latest_pose = None

        self.ros = roslibpy.Ros(host=ROBOT_IP, port=ROBOT_PORT)

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        print("[Telemetry] Connecting to rosbridge...")
        self.ros.run()
        print("[Telemetry] Connected.")

        map_topic = roslibpy.Topic(self.ros, "/map", "nav_msgs/OccupancyGrid")
        map_topic.subscribe(self._handle_map)

        odom_topic = roslibpy.Topic(self.ros, "/odom", "nav_msgs/Odometry")
        odom_topic.subscribe(self._handle_odom)

    def _handle_map(self, msg):
        with self._map_lock:
            if self._map_ready:
                return
            self._map_info = msg["info"]
            self._map_data = msg["data"]
            self._map_ready = True
            print("[Telemetry] /map received.")

    def _handle_odom(self, msg):
        pos = msg["pose"]["pose"]["position"]
        ori = msg["pose"]["pose"]["orientation"]
        twist = msg["twist"]["twist"]

        x = pos["x"]
        y = pos["y"]

        qx, qy, qz, qw = ori["x"], ori["y"], ori["z"], ori["w"]
        siny = 2 * (qw * qz + qx * qy)
        cosy = 1 - 2 * (qy * qy + qz * qz)
        yaw_deg = math.degrees(math.atan2(siny, cosy))

        speed = twist["linear"]["x"]

        with self._pose_lock:
            self._latest_pose = (x, y, yaw_deg, speed)

    def get_map(self):
        with self._map_lock:
            if not self._map_ready:
                return None, None
            return self._map_info, self._map_data

    def get_pose(self):
        with self._pose_lock:
            return self._latest_pose
