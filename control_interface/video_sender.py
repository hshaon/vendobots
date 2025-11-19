import cv2
import socket
import numpy as np
import time

# --- UDP Video Stream Parameters ---
# IMPORTANT: This IP address MUST be the ACTUAL local IP address of the 
# device running the PyQt 'control_interface.py' (the RECEIVER).
# Example: "192.168.1.50"
UDP_IP = "127.0.0.1" 
UDP_PORT = 5005      # Must match the port defined in control_interface.py
MAX_UDP_PACKET = 65000 # Max UDP payload size (65535 bytes) - keep slightly under for overhead.

def video_streamer():
    """
    Captures video from the local webcam, encodes it as JPEG, and sends it via UDP.
    """
    # Initialize the video capture object (0 is typically the default webcam)
    cap = cv2.VideoCapture(0)
    
    # Optional: Set resolution to 640x480 for consistency (the size used in the GUI)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_PROP_FRAME_HEIGHT, 480)
    
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

            # 2. Encode the frame to JPEG bytes (compression is necessary for fast UDP transfer)
            # JPEG quality 90/100 is a good balance of size and quality
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90] 
            _, jpeg_buffer = cv2.imencode('.jpg', frame, encode_param)
            data = jpeg_buffer.tobytes()
            
            # 3. Send the data over UDP
            if len(data) < MAX_UDP_PACKET:
                sender_socket.sendto(data, (UDP_IP, UDP_PORT))
            else:
                # This should ideally not happen for 640x480 resolution
                print(f"Warning: Frame size ({len(data)} bytes) exceeds max UDP packet size. Frame dropped.")
            
            # Control the frame rate (approx. 30 FPS)
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


if __name__ == '__main__':
    video_streamer()