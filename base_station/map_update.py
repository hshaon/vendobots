import time
import requests
import roslibpy
import threading

# Robot Connection
ROBOT_IP = "192.168.2.115"
ROBOT_PORT = 9090

# Backend Connection
API_BASE_URL = "http://192.168.2.129:8000" 
ROBOT_ID = 1

# 3. Settings
SYNC_INTERVAL = 1.0

class MapUpdate:
    def __init__(self):
        self.client = roslibpy.Ros(host=ROBOT_IP, port=ROBOT_PORT)
        self.latest_x = 0.0
        self.latest_y = 0.0
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        print(f"[Agent] Connecting to Robot at {ROBOT_IP}...")
        try:
            self.client.run()
            print("[Agent] Connected to ROS Bridge.")
        except Exception as e:
            print(f"[Agent] Failed to connect to ROS: {e}")
            return

        # Subscribe to Odometry to get position
        listener = roslibpy.Topic(self.client, '/odom', 'nav_msgs/Odometry')
        listener.subscribe(self._odom_callback)

        print(f"[Agent] Starting Sync Loop (Target: {API_BASE_URL})...")
        print("[Agent] Press Ctrl+C to stop.")
        
        try:
            while self.client.is_connected and self.running:
                self._sync_to_db()
                time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            print("\n[Agent] Stopping...")
        finally:
            listener.unsubscribe()
            self.client.terminate()

    def _odom_callback(self, msg):
        """Callback that receives live position from Robot."""
        pos = msg['pose']['pose']['position']
        
        with self.lock:
            self.latest_x = pos['x']
            self.latest_y = pos['y']

    def _sync_to_db(self):
        """Sends the latest position to the Backend API."""
        with self.lock:
            x = self.latest_x
            y = self.latest_y

        try:
            url = f"{API_BASE_URL}/robots/{ROBOT_ID}/position"
            payload = {
                "current_pos_x": x,
                "current_pos_y": y
            }
            
            # Send PUT request
            response = requests.put(url, json=payload, timeout=0.5)
            
            if response.status_code == 200:
                print(f"[Sync] OK -> Pos: ({x:.2f}, {y:.2f})")
            else:
                print(f"[Sync] API Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("[Sync] Failed: Could not connect to Backend API.")
        except Exception as e:
            print(f"[Sync] Error: {e}")

if __name__ == "__main__":
    agent = MapUpdate()
    agent.start()