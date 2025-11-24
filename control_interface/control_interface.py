import sys
import threading
import socket
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QLineEdit,
    QGridLayout, QTextEdit
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import numpy as np
import cv2

# --- UDP Video Stream Parameters ---
UDP_IP = "10.22.49.84"
UDP_PORT = 5005
BUFFER_SIZE = 65536

class RobotControlInterface(QWidget):
    """
    Main application window for the robot control interface.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vendobots Robot Control Interface")
        self.setGeometry(100, 100, 1000, 600)
        self.video_label = QLabel("Waiting for Video Stream...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(640, 480) # Standard video size

        self.setup_ui()
        self.setup_udp()

        # Timer to update the video frame (important for GUI responsiveness)
        self.video_update_timer = QTimer(self)
        self.video_update_timer.timeout.connect(self.update_video_display)
        self.video_update_timer.start(30) # Update rate in ms (~33 FPS)
        self.latest_frame = None
        self.latest_frame_bytes = None

    def setup_ui(self):
        """Initializes all widgets and layouts."""
        main_layout = QHBoxLayout(self)

        # 1. Video and Control Column (Left)
        video_control_layout = QVBoxLayout()
        video_control_layout.addWidget(self.create_video_group())
        video_control_layout.addWidget(self.create_control_group())
        video_control_layout.addStretch(1)

        # 2. Status and Log Column (Right)
        status_log_layout = QVBoxLayout()
        status_log_layout.addWidget(self.create_status_group())
        status_log_layout.addWidget(self.create_log_group())
        status_log_layout.addStretch(1)

        main_layout.addLayout(video_control_layout, 2)
        main_layout.addLayout(status_log_layout, 1)

    # --- Group Box Creation Methods ---

    def create_video_group(self):
        """Creates the Video Stream Group Box."""
        video_group = QGroupBox("Video Stream")
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)

        # Simple controls for the UDP stream
        self.start_udp_button = QPushButton("Start UDP Listen")
        self.start_udp_button.clicked.connect(self.start_udp)
        self.stop_udp_button = QPushButton("Stop UDP Listen")
        self.stop_udp_button.clicked.connect(self.stop_udp)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.start_udp_button)
        h_layout.addWidget(self.stop_udp_button)
        layout.addLayout(h_layout)

        video_group.setLayout(layout)
        return video_group

    def create_control_group(self):
        """Creates the Manual Control Group Box with D-pad style buttons."""
        control_group = QGroupBox("Manual Control")
        layout = QGridLayout()

        # Movement Buttons
        self.move_forward = QPushButton("Forward")
        self.move_backward = QPushButton("Backward")
        self.turn_left = QPushButton("Left")
        self.turn_right = QPushButton("Right")
        self.stop = QPushButton("Stop")

        # Layout using a D-pad arrangement
        layout.addWidget(self.move_forward, 0, 1)
        layout.addWidget(self.turn_left, 1, 0)
        layout.addWidget(self.stop, 1, 1)
        layout.addWidget(self.turn_right, 1, 2)
        layout.addWidget(self.move_backward, 2, 1)

        # Connect button signals (example functions)
        self.move_forward.clicked.connect(lambda: self.send_command("FORWARD"))
        self.move_backward.clicked.connect(lambda: self.send_command("BACKWARD"))
        self.turn_left.clicked.connect(lambda: self.send_command("LEFT"))
        self.turn_right.clicked.connect(lambda: self.send_command("RIGHT"))
        self.stop.clicked.connect(lambda: self.send_command("STOP"))

        control_group.setLayout(layout)
        return control_group

    def create_status_group(self):
        """Creates the Robot Status Group Box."""
        status_group = QGroupBox("Robot Status")
        layout = QGridLayout()

        # Status labels
        self.robot_id_label = QLabel("Robot ID:")
        self.battery_label = QLabel("Battery Level:")
        self.location_label = QLabel("Current Location:")
        self.status_label = QLabel("Status:")

        # Status values (for display, typically updated from robot data)
        self.robot_id_value = QLabel("Vbot-001")
        self.battery_value = QLabel("75%")
        self.location_value = QLabel("(0.0, 0.0)")
        self.status_value = QLabel("Idle")

        # Arrange labels and values
        layout.addWidget(self.robot_id_label, 0, 0)
        layout.addWidget(self.robot_id_value, 0, 1)
        layout.addWidget(self.battery_label, 1, 0)
        layout.addWidget(self.battery_value, 1, 1)
        layout.addWidget(self.location_label, 2, 0)
        layout.addWidget(self.location_value, 2, 1)
        layout.addWidget(self.status_label, 3, 0)
        layout.addWidget(self.status_value, 3, 1)

        status_group.setLayout(layout)
        return status_group

    def create_log_group(self):
        """Creates the Log/Command Output Group Box."""
        log_group = QGroupBox("System Log / Command Output")
        layout = QVBoxLayout()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFontPointSize(8)
        layout.addWidget(self.log_text_edit)
        log_group.setLayout(layout)
        return log_group

    # --- UDP Methods ---

    def setup_udp(self):
        """Initializes UDP socket and threading variables."""
        self.udp_thread = None
        self.is_listening = False
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            self.log_message(f"Error setting up UDP socket: {e}")
            self.udp_socket = None

    def start_udp(self):
        """Starts the UDP listener thread."""
        if not self.udp_socket:
            self.log_message("UDP Socket not available. Cannot start listening.")
            return

        if self.is_listening:
            self.log_message("UDP Listener is already running.")
            return

        try:
            self.udp_socket.bind((UDP_IP, UDP_PORT))
            self.is_listening = True
            self.udp_thread = threading.Thread(target=self.udp_listener, daemon=True)
            self.udp_thread.start()
            self.log_message(f"Started listening for UDP stream on {UDP_IP}:{UDP_PORT}")
            self.video_label.setText("Listening for stream...")
        except Exception as e:
            self.is_listening = False
            self.log_message(f"Failed to bind/start UDP: {e}")

    def stop_udp(self):
        """Stops the UDP listener thread."""
        if self.is_listening:
            self.is_listening = False
            if self.udp_thread and self.udp_thread.is_alive():
                self.udp_thread.join(1) # Wait up to 1 second
            self.log_message("Stopped UDP Listener.")
            self.video_label.setText("Waiting for Video Stream...")
        else:
            self.log_message("UDP Listener is not running.")

    def udp_listener(self):
        """Thread function to receive and process UDP video data."""
        self.log_message("UDP thread running. Waiting for data.")
        
        # Buffer to hold the incoming JPEG bytes from the sender
        self.latest_frame_bytes = None

        while self.is_listening:
            try:
                # Receive a single packet (expecting a single compressed frame)
                data, addr = self.udp_socket.recvfrom(BUFFER_SIZE)
                
                if len(data) > 0:
                    # Store the raw bytes received. The GUI thread will handle decoding.
                    self.latest_frame_bytes = data 
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_listening:
                    self.log_message(f"UDP Receive Error: {e}")
                break
        self.log_message("UDP thread finished.")

    def update_video_display(self):
        """Updates the QLabel with the latest received frame by decoding JPEG."""
        # Use a temporary variable and consume the frame data from the listener thread
        current_frame_bytes = self.latest_frame_bytes
        self.latest_frame_bytes = None 

        if current_frame_bytes is not None:
            try:
                # 1. Convert the raw JPEG bytes back into a NumPy array
                np_buffer = np.frombuffer(current_frame_bytes, dtype=np.uint8)
                
                # 2. Decode the JPEG image buffer into a full BGR image array
                frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)

                if frame is None:
                    # This happens if the JPEG buffer is corrupt or incomplete
                    return

                # Convert the OpenCV image (BGR) to an RGB format needed for QImage
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert NumPy array (RGB) to QImage
                height, width, channel = rgb_image.shape
                bytesPerLine = 3 * width
                qImg = QImage(
                    rgb_image.data, 
                    width, 
                    height, 
                    bytesPerLine, 
                    QImage.Format_RGB888
                )

                # Display the image
                pixmap = QPixmap.fromImage(qImg)
                scaled_pixmap = pixmap.scaled(
                    self.video_label.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)

            except Exception as e:
                self.log_message(f"Frame Processing Error: {e}")

    # --- Communication/Command Methods ---

    def send_command(self, command):
        """Simulates sending a command to the robot and logs it."""
        self.log_message(f"COMMAND SENT: {command}")
        # currently just temporary

    def log_message(self, message):
        """Appends a message to the log area."""
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_text_edit.append(f"{timestamp} {message}")


# --- Main Execution ---

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RobotControlInterface()
    window.show()
    sys.exit(app.exec_())