import socketio
from dotenv import load_dotenv
import os
import threading
import time
import cv2
import datetime
import requests

from flask import Flask, Response
from pyngrok import ngrok
import logging
logging.basicConfig(level=logging.DEBUG)

# import requests
# requests.get('https://hricameratest.onrender.com')
# try:
#     r = requests.get('https://hricameratest.onrender.com', timeout=5)
#     print(f"Server reachable: {r.status_code}")
# except requests.RequestException as e:
#     print(f"⚠️ Cannot reach server: {e}")
# Start ngrok tunnel
public_url = ngrok.connect(8000)
print(f"\n🚀 Public Preview URL: {public_url}/preview\n")

sio = socketio.Client(logger=True, engineio_logger=True)
flask_app = Flask(__name__)
IDRobot = '1'  # Global variable to store robot id

# Load the .env file
load_dotenv()

# Access the environment variables
robot_id = os.getenv("ID_ROBOT")
backend_url = os.getenv("BE_URL")

class CameraController:
    def __init__(self):
        self.cap = None
        self.out = None
        self.recording = False
        self.record_thread = None
        self.lock = threading.Lock()  # For thread-safe access to the camera
        self.filename = None

    def open_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            if self.cap.isOpened():
                return "Camera opened"
            else:
                return "Failed to open camera"
        return "Camera already opened"

    def close_camera(self):
        if self.cap is not None:
            self.stop_recording()
            self.cap.release()
            self.cap = None
            return "Camera closed"
        return "Camera already closed"

    def start_recording(self): 
        if self.cap is None or not self.cap.isOpened(): 
            return "Camera not opened" 
        if self.recording: 
            return "Recording is activated" 
 
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        self.filename = f"Robot{IDRobot}_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.out = cv2.VideoWriter(f'output_{self.filename}.mp4', fourcc, 20.0, (640, 480)) 
        self.recording = True 
        self.record_thread = threading.Thread(target=self._record_loop) 
        self.record_thread.start() 
        return "Recording started"

    def stop_recording(self, dateCreated):
        if self.recording:
            self.recording = False
            self.record_thread.join()
            if self.out:
                self.out.release()
                self.out = None
                if dateCreated != 'NONE':
                    print(self.filename)
                    url = f"{backend_url}/{dateCreated}"
                    data = {"video_url": self.filename}
                    try:
                        response = requests.post(url, json=data)
                        response.raise_for_status()  # raise exception for HTTP errors
                        print("Video URL sent successfully:", response.json())
                    except requests.RequestException as e:
                        print("Failed to send video URL:", e)
                self.filename = None
            return "Recording stopped"
        return "Not currently recording"

    def _record_loop(self):
        while self.recording and self.cap and self.cap.isOpened():
            with self.lock:
                ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (640, 480))
            if self.out:
                self.out.write(frame)
            time.sleep(0.05)  # ~20fps

    def generate_frames(self):
        while self.cap and self.cap.isOpened():
            with self.lock:
                ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (800, 540)) #(320, 240)
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)  # ~10fps

camera_controller = CameraController()

# Socket.IO Events
@sio.event
def connect():
    global IDRobot
    print('✅ Connected to server')
    sio.emit('join', {'room': IDRobot})

@sio.event
def disconnect():
    print('❌ Disconnected from server')

@sio.event
def connect_error(data):
    print("❌ Connection failed:", data)

@sio.on('camera_action')
def on_camera_action(data):
    action = data.get('action')
    dateCreated = data.get('dateCreated')

    if action:
        action = action.lower()
        if action == 'open':
            message = camera_controller.open_camera()
        elif action == 'close':
            message = camera_controller.close_camera()
        elif action == 'start':
            message = camera_controller.start_recording()
        elif action == 'stop':
            message = camera_controller.stop_recording(dateCreated)
        else:
            message = "❓ Unknown action"
        print(f"🔧 {message}")
    else:
        print("⚠️ No action received")

# Flask route for MJPEG preview
@flask_app.route('/preview')
def preview():
    if camera_controller.cap is None or not camera_controller.cap.isOpened():
        camera_controller.open_camera()
    return Response(camera_controller.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Flask server
def start_flask_server():
    flask_app.run(host='0.0.0.0', port=7000, debug=False, use_reloader=False)

# SocketIO runner
def run_socketio(api_url):
    print(f"Connecting to SocketIO server at {api_url}...")
    sio.connect(api_url)#, transports=['websocket'], namespaces=['/'])
    sio.wait()
    
# Main entry
if __name__ == '__main__':
    api_url = 'https://hricameratest.onrender.com'
    socketio_thread = threading.Thread(target=run_socketio, args=(api_url,))
    socketio_thread.daemon = True
    socketio_thread.start()

    start_flask_server()
