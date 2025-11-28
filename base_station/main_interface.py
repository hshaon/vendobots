import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSlider, QFrame,
    QLineEdit, QGraphicsDropShadowEffect, QSizePolicy
)

from send_movement import init_connection, send_cmd_vel, stop_robot


# ---------------------- Helper Card ----------------------

class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._add_shadow()

    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(shadow)


# ---------------------- Live Feed -------------------------

class LiveFeedWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video_label = QLabel("Video Stream")
        self.video_label.setObjectName("VideoArea")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setScaledContents(True)

        layout.addWidget(self.video_label)

# ---------------------- Map Widget ------------------------

class MapViewWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.map_label = QLabel("Map / Costmap")
        self.map_label.setObjectName("MapArea")
        self.map_label.setAlignment(Qt.AlignCenter)
        self.map_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.map_label)

# ---------------------- Telemetry -------------------------

class TelemetryWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        #layout.setContentsMargins(16, 16, 16, 16)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)

        self.text = QTextEdit()
        self.text.setObjectName("TelemetryText")
        self.text.setReadOnly(True)
        self.text.setFrameStyle(QFrame.NoFrame)
        self.text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text.viewport().setAutoFillBackground(False)

        self.text.setText(
            "Speed: 0 m/s\n"
            "Tilt: 0 deg\n"
            "Ch1 P: 10 N\n"
            "Ch2 P: 0 N\n"
        )

        layout.addWidget(self.text)




# ---------------------- Projection -------------------------

class ProjectionWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # ------------------- ICON BUTTON ROW -------------------
        icon_row = QHBoxLayout()
        icon_row.setSpacing(16)

        # icon file mapping
        icon_files = {
            "left": "icons/arrow_left.png",
            "up": "icons/arrow_up.png",
            "down": "icons/arrow_down.png",
            "right": "icons/arrow_right.png",
            "stop": "icons/stop.png"
        }

        for name, path in icon_files.items():
            b = QPushButton()
            b.setObjectName("ProjectionIconButton")
            b.setFixedSize(58, 58)
            b.setIconSize(QSize(32, 32))
            b.setIcon(QIcon(path))
            b.clicked.connect(lambda _, n=name: print(f"[Projection icon] {n} pressed"))
            icon_row.addWidget(b)

        # ------------------- TEXT FIELD -------------------
        self.textbox = QLineEdit()
        self.textbox.setPlaceholderText("Enter projection message...")
        self.textbox.setFixedHeight(42)
        self.textbox.setObjectName("ProjectionText")

        # ------------------- SHOW & CLEAR BUTTONS -------------------
        buttons = QHBoxLayout()
        buttons.setSpacing(16)

        show = QPushButton("Show")
        show.setObjectName("ProjectionButton")
        show.setFixedHeight(44)
        show.clicked.connect(lambda: print("[Projection] Show pressed"))

        clear = QPushButton("Clear")
        clear.setObjectName("ProjectionButton")
        clear.setFixedHeight(44)
        clear.clicked.connect(lambda: print("[Projection] Clear pressed"))

        buttons.addStretch()
        buttons.addWidget(show)
        buttons.addSpacing(12)
        buttons.addWidget(clear)
        buttons.addStretch()

        # ------------------- FINAL LAYOUT -------------------
        layout.addLayout(icon_row)
        layout.addWidget(self.textbox)
        layout.addLayout(buttons)


# ---------------------- Joystick ---------------------------

class JoystickWidget(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

        # Outer layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ---------------- SPEAKER + TALK ----------------
        row = QHBoxLayout()
        speaker = QPushButton("Speaker")
        speaker.setObjectName("SpeakerButton")
        speaker.clicked.connect(lambda: print("[AUDIO] Speaker"))

        talk = QPushButton("Talk")
        talk.setObjectName("MicButton")
        talk.clicked.connect(lambda: print("[AUDIO] Talk"))

        row.addWidget(speaker)
        row.addWidget(talk)
        layout.addLayout(row)

        # ---------------- THROTTLE ----------------
        throttle_label = QLabel("Throttle")
        layout.addWidget(throttle_label)

        slider = QSlider(Qt.Horizontal)
        slider.valueChanged.connect(lambda v: print("[THROTTLE]", v))
        layout.addWidget(slider)

        # ---------------- JOYSTICK PAD ----------------
        pad = QFrame()
        pad.setObjectName("JoystickPad")
        pad.setFixedSize(240, 240)
        pad.setStyleSheet("background-color: #A7C8E8; border-radius: 120px;")
        pad_layout = QVBoxLayout(pad)
        pad_layout.setContentsMargins(0, 0, 0, 0)

        # ABSOLUTE LAYOUT INSIDE THE PAD
        container = QWidget(pad)
        container.setGeometry(0, 0, 240, 240)

        # helper for circular buttons
        def make_button(icon_file, cmd):
            b = QPushButton("", container)
            b.setObjectName("JoyBtn")
            b.setIcon(QIcon(icon_file))
            b.setIconSize(QSize(32, 32))
            b.setFixedSize(56, 56)
            b.setStyleSheet("""
                QPushButton#JoyBtn {
                    background: white;
                    border-radius: 28px;
                }
                QPushButton#JoyBtn:hover {
                    background: #f0f0f0;
                }
            """)
            b.clicked.connect(lambda _, c=cmd: self.callback(c))

            return b

        # Create buttons
        up_btn = make_button("icons/up.png", "up")
        down_btn = make_button("icons/down.png", "down")
        left_btn = make_button("icons/left.png", "left")
        right_btn = make_button("icons/right.png", "right")

        # CENTER STOP BUTTON
        center_btn = QPushButton("", container)
        center_btn.setObjectName("JoyCenter")
        center_btn.setIcon(QIcon("icons/stop.png"))
        center_btn.setIconSize(QSize(36, 36))
        center_btn.setFixedSize(70, 70)
        center_btn.setStyleSheet("""
            QPushButton#JoyCenter {
                background: #E34F4F;
                border-radius: 35px;
            }
            QPushButton#JoyCenter:hover {
                background: #D13C3C;
            }
        """)
        center_btn.clicked.connect(lambda: self.callback("stop"))


        # ---------------- POSITION BUTTONS MANUALLY ----------------
        # Center of pad = (120, 120)
        center_btn.move(120 - 35, 120 - 35)      # (x - half, y - half)

        up_btn.move(120 - 28, 40 - 28)
        down_btn.move(120 - 28, 200 - 28)
        left_btn.move(40 - 28, 120 - 28)
        right_btn.move(200 - 28, 120 - 28)

        # Add pad to layout
        layout.addWidget(pad, alignment=Qt.AlignCenter)


# ---------------------- Main Window ------------------------

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vendobot Remote Control")
        self.resize(1300, 850)
        self.setup_styles()
        
        # Connect with ROS-Bridge
        init_connection()

        # ======================================================
        #                     LIVE FEED BLOCK
        # ======================================================

        live_title_row = QHBoxLayout()
        dot = QLabel()
        dot.setObjectName("LiveDot")
        dot.setFixedSize(12, 12)

        title = QLabel("Live Feed")
        title.setObjectName("TitleLabel")

        live_title_row.addWidget(dot)
        live_title_row.addWidget(title)
        live_title_row.addStretch()

        live_card = Card()
        live_layout = QVBoxLayout(live_card)
        live_layout.setContentsMargins(0, 0, 0, 0)
        live_layout.setSpacing(0)
        live_layout.addWidget(LiveFeedWidget())

        live_container = QVBoxLayout()
        live_container.setSpacing(6)
        live_container.addLayout(live_title_row)
        live_container.addWidget(live_card)

        # ======================================================
        #                     MAP BLOCK
        # ======================================================

        map_title_row = QHBoxLayout()
        map_title = QLabel("Map View")
        map_title.setObjectName("TitleLabel")

        map_title_row.addWidget(map_title)
        map_title_row.addStretch()

        map_card = Card()
        map_layout = QVBoxLayout(map_card)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(0)
        map_layout.addWidget(MapViewWidget())

        map_container = QVBoxLayout()
        map_container.setSpacing(6)
        map_container.addLayout(map_title_row)
        map_container.addWidget(map_card)

        # ======================================================
        #                     TOP ROW
        # ======================================================

        top_row = QHBoxLayout()
        top_row.setSpacing(24)
        top_row.addLayout(live_container, 3)
        top_row.addLayout(map_container, 3)

        # ======================================================
        #                     TELEMETRY BLOCK
        # ======================================================

        tele_title_row = QHBoxLayout()
        tele_title = QLabel("Data")
        tele_title.setObjectName("TitleLabel")
        tele_title_row.addWidget(tele_title)
        tele_title_row.addStretch()

        tele_card = Card()
        tele_layout = QVBoxLayout(tele_card)
        tele_layout.setContentsMargins(0, 0, 0, 0)
        tele_layout.setSpacing(0)
        tele_layout.addWidget(TelemetryWidget())

        tele_container = QVBoxLayout()
        tele_container.setSpacing(6)
        tele_container.addLayout(tele_title_row)
        tele_container.addWidget(tele_card)

        # ======================================================
        #                    PROJECTION BLOCK
        # ======================================================

        proj_title_row = QHBoxLayout()
        proj_title = QLabel("Projection")
        proj_title.setObjectName("TitleLabel")
        proj_title_row.addWidget(proj_title)
        proj_title_row.addStretch()

        proj_card = Card()
        proj_layout = QVBoxLayout(proj_card)
        proj_layout.setContentsMargins(0, 0, 0, 0)
        proj_layout.setSpacing(0)
        proj_layout.addWidget(ProjectionWidget())

        proj_container = QVBoxLayout()
        proj_container.setSpacing(6)
        proj_container.addLayout(proj_title_row)
        proj_container.addWidget(proj_card)

        # ======================================================
        #                    JOYSTICK BLOCK
        # ======================================================

        joy = JoystickWidget(self.handle_teleop)

        # ======================================================
        #                      BOTTOM ROW
        # ======================================================

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(24)
        bottom_row.addLayout(tele_container, 2)
        bottom_row.addLayout(proj_container, 3)
        bottom_row.addWidget(joy, 3)

        # ======================================================
        #                      MAIN LAYOUT
        # ======================================================

        main = QVBoxLayout(self)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(24)

        main.addLayout(top_row, 3)
        main.addLayout(bottom_row, 3)
        
    def handle_teleop(self, cmd):
        # throttle from slider later; for now fixed 0.3 m/s
        linear_speed = 0.30
        angular_speed = 1.0

        if cmd == "up":
            send_cmd_vel(linear_speed, 0.0)

        elif cmd == "down":
            send_cmd_vel(-linear_speed, 0.0)

        elif cmd == "left":
            send_cmd_vel(0.0, angular_speed)

        elif cmd == "right":
            send_cmd_vel(0.0, -angular_speed)

        elif cmd == "stop":
            stop_robot()


    def setup_styles(self):
        self.setStyleSheet("""
        QWidget {
            background: #E6E8EA;
            font-family: Segoe UI;
        }

        #Card {
            background: white;
            border-radius: 24px;
        }

        #VideoArea {
            background: black;
            border-radius: 24px;
        }

        #MapArea {
            background: #C7E4E3;
            border-radius: 24px;
        }

        #LiveDot {
            background: red;
            border-radius: 6px;
        }

        #TitleLabel {
            font-size: 14px;
            color: #555;
        }

        QPushButton {
            background: #B29CFF;
            color: white;
            border-radius: 16px;
            padding: 10px 18px;
        }

        #JoystickPad {
            background: #A7C8E8;
            border-radius: 110px;
        }

        #JoystickButton {
            background: white;
            border-radius: 20px;
        }

        #StopButton {
            background: #E34F4F;
            border-radius: 32px;
        }
        
        /* Projection icon button using images */
        #ProjectionIconButton {
            background: #D8C6FF;
            border-radius: 16px;
            border: none;
        }

        #ProjectionIconButton:hover {
            background: #C2B0FF;
        }

        /* Projection text input */
        #ProjectionText {
            background: #FFFFFF;
            border-radius: 12px;
            border: 1px solid #CFCFCF;
            padding-left: 12px;
            padding-right: 12px;
            font-size: 15px;
        }

        /* Show / Clear buttons */
        #ProjectionButton {
            background: #B29CFF;
            color: white;
            font-size: 15px;
            border-radius: 16px;
            padding: 6px 18px;
        }

        #ProjectionButton:hover {
            background: #9A85E8;
        }
        
        #TelemetryText {
            background: #F7F8FA;
            border: none;
            border-radius: 14px;
            padding: 12px;
            font-size: 15px;
            color: #333;
        }

        #TelemetryText:focus {
            outline: none;
            border: none;
        }


        """)

# ---------------------- Main ------------------------------

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
