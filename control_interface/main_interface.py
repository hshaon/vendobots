import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSlider, QFrame,
    QLineEdit, QGraphicsDropShadowEffect, QSizePolicy
)

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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Icon row
        icons = QHBoxLayout()
        icons.setSpacing(8)

        for sym in ["←", "↑", "↓", "→", "◼"]:
            b = QPushButton(sym)
            b.setObjectName("ProjectionIconButton")
            b.setFixedSize(40, 40)
            b.clicked.connect(lambda _, s=sym: print(f"[Icon] {s} pressed"))
            icons.addWidget(b)

        self.textbox = QLineEdit()
        self.textbox.setPlaceholderText("Stopping")

        # Buttons
        buttons = QHBoxLayout()
        show = QPushButton("Show")
        clear = QPushButton("Clear")

        show.clicked.connect(lambda: print("[Projection] Show"))
        clear.clicked.connect(lambda: print("[Projection] Clear"))

        buttons.addWidget(show)
        buttons.addWidget(clear)
        buttons.addStretch()

        layout.addLayout(icons)
        layout.addWidget(self.textbox)
        layout.addLayout(buttons)

# ---------------------- Joystick ---------------------------

class JoystickWidget(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        row = QHBoxLayout()
        speaker = QPushButton("Speaker")
        speaker.setObjectName("SpeakerButton")
        talk = QPushButton("Talk")
        talk.setObjectName("MicButton")
        row.addWidget(speaker)
        row.addWidget(talk)

        throttle_label = QLabel("Throttle")
        slider = QSlider(Qt.Horizontal)

        pad = QFrame()
        pad.setObjectName("JoystickPad")
        pad.setFixedSize(220, 220)
        grid = QGridLayout(pad)
        grid.setContentsMargins(40, 40, 40, 40)

        def jb(sym):
            b = QPushButton(sym)
            b.setObjectName("JoystickButton")
            b.setFixedSize(40, 40)
            return b

        btn_up = jb("↑")
        btn_down = jb("↓")
        btn_left = jb("←")
        btn_right = jb("→")

        center = QPushButton("")
        center.setObjectName("StopButton")
        center.setFixedSize(64, 64)

        grid.addWidget(btn_up, 0, 1)
        grid.addWidget(btn_left, 1, 0)
        grid.addWidget(center, 1, 1)
        grid.addWidget(btn_right, 1, 2)
        grid.addWidget(btn_down, 2, 1)

        layout.addLayout(row)
        layout.addWidget(throttle_label)
        layout.addWidget(slider)
        layout.addWidget(pad, alignment=Qt.AlignCenter)

# ---------------------- Main Window ------------------------

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vendobot Remote Control")
        self.resize(1300, 850)
        self.setup_styles()

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
        print("CMD:", cmd)

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
        """)

# ---------------------- Main ------------------------------

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
