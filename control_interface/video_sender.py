import cv2
import socket
import numpy as np
import time
import os
import threading
import socketio
from dotenv import load_dotenv
from datetime import datetime
from EmotionEvaluation import satisficationEvaluation
import requests

current_folder = os.path.dirname(os.path.abspath(__file__))
record_folder = os.path.join(current_folder, "transaction_records")
current_video_file = None

out = None
recording = False

statusRecording = None

# Load the .env file
load_dotenv()

# Access the environment variables
robot_id = os.getenv("ID_ROBOT")
backend_url = os.getenv("BE_URL")
control_camera_url = os.getenv("CONTROL_CAMERA_URL")

UDP_IP = "192.168.2.113" # IP must match that of the receiver
UDP_PORT = 5005 # Must match the port defined in control_interface.py
MAX_UDP_PACKET = 65000

frame_width = 640
frame_height = 480
fps = 30
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 

save_path = ""
videourl = None

def start_record():
    global out, recording, save_path
    # Video output path
    save_path = os.path.join(
    record_folder,
    f"{current_video_file.replace(' ','_').replace(':','_').replace('-','_')}.mp4")


    # Initialize VideoWriter
    out = cv2.VideoWriter(save_path, fourcc, fps, (frame_width, frame_height))
    recording = True
    print(f"Recording started: {save_path}")
    if not out.isOpened():
        print("Error: VideoWriter failed to open!")
    else:
        print("yes")
    return out

# Function to stop recording
def stop_record():
    global out, recording, statusRecording, videourl
    if out:
        out.release()
        out = None
        if videourl != 'NONE':
            send_videourl = videourl+","+save_path
           
            url = f"{backend_url}/deliveryRecord/updateVideoURL"
            data = {"video_url": send_videourl}
            try:
                response = requests.post(url, json=data)
                response.raise_for_status()  # raise exception for HTTP errors
                print("Video URL sent successfully:")
                
                thread = threading.Thread(target=satisficationEvaluation, args=(save_path,), daemon=True)
                thread.start()
            except requests.RequestException as e:
                print("Failed to send video URL:", e)
    recording = False
    statusRecording = None
    print("Recording stopped.")
    
def video_streamer():
    """
    Captures video from the local webcam, encodes it as JPEG, and sends it via UDP.
    """
    # Initialize the video capture object
    cap = cv2.VideoCapture(0)
    
    # setting camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
    # Create a UDP socket for sending data
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    if not cap.isOpened():
        print("Error: Could not open webcam. Check if another app is using it or if the camera ID is correct.")
        return

    print(f"Starting video stream sender to {UDP_IP}:{UDP_PORT}...")
    try:
        while True:
            # 1. Capture the raw frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            # 2. Encode the frame to JPEG bytes
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90] 
            _, jpeg_buffer = cv2.imencode('.jpg', frame, encode_param)
            data = jpeg_buffer.tobytes()
            
            if statusRecording == "start" and not recording:
                start_record()
            elif statusRecording == "stop" and recording:
                stop_record()
                
            if recording and out:
                out.write(frame)

            # 3. Send the data over UDP
            if len(data) < MAX_UDP_PACKET:
                sender_socket.sendto(data, (UDP_IP, UDP_PORT))
            else:
                print(f"Warning: Frame size ({len(data)} bytes) exceeds max UDP packet size. Frame dropped.")
            
            # Control the frame rate
            time.sleep(1/30) 

    except KeyboardInterrupt:
        print("Streamer stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"An unexpected error occurred in the streamer: {e}")
    finally:
        # Clean up resources
        cap.release()
        sender_socket.close()
        print("Video streamer resources released.")


#Tuan add
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")
    sio.emit("join", {"room": robot_id})

@sio.event
def disconnect():
    print("❌ Disconnected from server")

def start_socketio():
    """Run the socket.io client in background thread"""
    try:
        print("Connecting to socket:", control_camera_url)
        sio.connect(control_camera_url, transports=['websocket'])
        sio.wait()
    except Exception as e:
        print("Socket.IO Error:", e)

@sio.on('camera_action')
def on_camera_action(data):
    action = data.get('action')
    receivedVideoUrl = data.get('videourl')
    
    if action == "start":
        num_files = len(os.listdir(record_folder)) 

        now = datetime.now().replace(microsecond=0)

        global current_video_file
        current_video_file =  f"transaction{num_files + 1}_{now}"
        
    global statusRecording,  videourl
    statusRecording = action
    videourl  = receivedVideoUrl

    print(f"action:{action}, videourl:{videourl}")
       
if __name__ == '__main__':
    
    sio_thread = threading.Thread(target=start_socketio, daemon=True)
    sio_thread.start()
    video_streamer()
    