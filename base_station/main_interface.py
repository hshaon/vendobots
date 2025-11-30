import sys
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon, QPolygonF, QTransform, QImage, QPainterPath
from PyQt5.QtCore import QSize, Qt, QTimer, QPointF, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QToolButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QSlider, QFrame,
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

# class LiveFeedWidget(QWidget):
#     def __init__(self):
#         super().__init__()

#         #from gi.repository import Gst, GLib
#         import gi
#         gi.require_version("Gst", "1.0")
#         from gi.repository import Gst, GLib
#         import numpy as np

#         self.Gst = Gst
#         self.GLib = GLib
#         self.np = np

#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)

#         self.video_label = QLabel("Connecting...")
#         self.video_label.setAlignment(Qt.AlignCenter)
#         self.video_label.setScaledContents(True)
#         self.video_label.setObjectName("VideoArea")
#         layout.addWidget(self.video_label)

#         # Initialize GStreamer
#         Gst.init(None)

#         # PIPELINE WORKS EXACTLY LIKE THE gst-launch VERSION
#         pipeline_str = (
#             "udpsrc port=5000 caps=\"application/x-rtp, media=video, encoding-name=H264, payload=96\" ! "
#             "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
#             "video/x-raw,format=RGB ! appsink name=appsink emit-signals=true sync=false max-buffers=1 drop=true"
#         )

#         self.pipeline = Gst.parse_launch(pipeline_str)

#         self.appsink = self.pipeline.get_by_name("appsink")
#         self.appsink.connect("new-sample", self.on_new_sample)

#         self.pipeline.set_state(Gst.State.PLAYING)

#         # Timer to keep GStreamer processing
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.gst_step)
#         self.timer.start(5)

#     def gst_step(self):
#         # Let GStreamer process internal messages (avoids freezes)
#         bus = self.pipeline.get_bus()
#         msg = bus.poll(self.Gst.MessageType.ANY, 0)
#         # we ignore msg content; we only want the pump

#     def on_new_sample(self, sink):
#         sample = sink.emit("pull-sample")
#         buf = sample.get_buffer()
#         caps = sample.get_caps()
#         w = caps.get_structure(0).get_value("width")
#         h = caps.get_structure(0).get_value("height")

#         success, map_info = buf.map(self.Gst.MapFlags.READ)
#         if not success:
#             return self.Gst.FlowReturn.ERROR

#         frame = self.np.ndarray(
#             shape=(h, w, 3),
#             dtype=self.np.uint8,
#             buffer=map_info.data
#         )

#         # Convert to QImage → QLabel
#         qimg = QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888)


#         # self.video_label.setPixmap(QPixmap.fromImage(qimg)) # uncomment if rectanfular 

#         # code for rounded corner in live feed. Start------------
#         pix = QPixmap.fromImage(qimg)
#         rounded = QPixmap(pix.size())
#         rounded.fill(Qt.transparent)

#         p = QPainter(rounded)
#         p.setRenderHint(QPainter.Antialiasing)
#         path = QPainterPath()
#         path.addRoundedRect(0, 0, pix.width(), pix.height(), 24, 24)
#         p.setClipPath(path)
#         p.drawPixmap(0, 0, pix)
#         p.end()

#         self.video_label.setPixmap(rounded)
#         # code for rounded corner in live feed. End---------------


#         buf.unmap(map_info)
#         return self.Gst.FlowReturn.OK

#     def closeEvent(self, event):
#         self.pipeline.set_state(self.Gst.State.NULL)
#         super().closeEvent(event)


class LiveFeedWidget(QWidget):
    new_frame = pyqtSignal(QImage)   # <-- Qt-safe signal

    def __init__(self):
        super().__init__()

        import gi
        gi.require_version("Gst", "1.0")
        from gi.repository import Gst, GLib
        import numpy as np

        self.Gst = Gst
        self.GLib = GLib
        self.np = np

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("Connecting...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setScaledContents(True)
        layout.addWidget(self.video_label)

        # Connect signal to Qt GUI slot
        self.new_frame.connect(self.update_gui_frame)

        Gst.init(None)

        pipeline_str = (
            "udpsrc port=5000 caps=\"application/x-rtp, media=video, encoding-name=H264, payload=96\" ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "video/x-raw,format=RGB ! appsink name=appsink emit-signals=true sync=false max-buffers=1 drop=true"
        )

        self.pipeline = Gst.parse_launch(pipeline_str)
        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.connect("new-sample", self.on_new_sample)

        self.pipeline.set_state(Gst.State.PLAYING)

        # Keep GStreamer pumping
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.gst_step)
        self.timer.start(5)

    def gst_step(self):
        bus = self.pipeline.get_bus()
        msg = bus.poll(self.Gst.MessageType.ANY, 0)

    def on_new_sample(self, sink):
        # This is running on GStreamer thread
        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        caps = sample.get_caps()
        w = caps.get_structure(0).get_value("width")
        h = caps.get_structure(0).get_value("height")

        success, map_info = buf.map(self.Gst.MapFlags.READ)
        if not success:
            return self.Gst.FlowReturn.ERROR

        frame = self.np.ndarray(
            shape=(h, w, 3),
            dtype=self.np.uint8,
            buffer=map_info.data
        )

        qimg = QImage(frame.data, w, h, 3 * w, QImage.Format_RGB888)
        buf.unmap(map_info)

        # Emit Qt signal (safe) → handled in main thread
        self.new_frame.emit(qimg)

        return self.Gst.FlowReturn.OK

    def update_gui_frame(self, qimg):
        # Now in Qt main thread → safe to draw
        pix = QPixmap.fromImage(qimg)
        rounded = QPixmap(pix.size())
        rounded.fill(Qt.transparent)

        p = QPainter(rounded)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pix.width(), pix.height(), 24, 24)
        p.setClipPath(path)
        p.drawPixmap(0, 0, pix)
        p.end()

        self.video_label.setPixmap(rounded)

    def closeEvent(self, event):
        self.pipeline.set_state(self.Gst.State.NULL)
        super().closeEvent(event)


# ---------------------- Map Widget ------------------------

class MapViewWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.rotated_pixmap = None
        self.origin_x = 0
        self.origin_y = 0
        self.resolution = 0.05
        self.rx = 0
        self.ry = 0
        self.yaw = 0

        # --- Status Overlay ---
        self.status = QLabel("Connecting to ROS…")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("""
            font-size: 15px;
            color: #555;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.status)

    def set_status(self, text):
        self.status.setText(text)
        self.status.show()
        self.rotated_pixmap = None   # force paintEvent to skip drawing map
        self.update()

    # Called once when map arrives
    def load_from_occupancy(self, map_info, data):
        self.set_status("Rendering map…")

        from PyQt5.QtGui import QImage, QPixmap, QColor

        width = map_info["width"]
        height = map_info["height"]

        print(f"[Map] Building image {width}x{height} ...")

        img = QImage(width, height, QImage.Format_Indexed8)
        gray = [QColor(i, i, i).rgb() for i in range(256)]
        img.setColorTable(gray)

        for y in range(height):
            base = y * width
            for x in range(width):
                v = data[base+x]
                if v == -1:
                    pix = 127
                elif v == 0:
                    pix = 255
                else:
                    pix = 0
                img.setPixel(x, y, pix)

        pixmap = QPixmap.fromImage(img)

        # rotate + flip map
        t = QTransform()
        t.rotate(-90)
        pm = pixmap.transformed(t, Qt.SmoothTransformation)
        flip = QTransform()
        flip.scale(-1,1)
        self.rotated_pixmap = pm.transformed(flip)

        self.resolution = map_info["resolution"]
        self.origin_x = map_info["origin"]["position"]["x"]
        self.origin_y = map_info["origin"]["position"]["y"]

        print("[Map] Ready, rotated size =", self.rotated_pixmap.size())

        # Map ready
        self.status.hide()
        self.update()

    def update_robot_pose(self, x, y, yaw_deg):
        self.rx = x
        self.ry = y
        self.yaw = yaw_deg
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.rotated_pixmap is None:
            # Only status label is shown
            return

        painter = QPainter(self)
        r = self.rect()

        scaled = self.rotated_pixmap.scaled(
            r.width(), r.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        x = (r.width() - scaled.width()) / 2
        y = (r.height() - scaled.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled)

        # Draw robot arrow
        map_w = self.rotated_pixmap.width()
        map_h = self.rotated_pixmap.height()

        px_map = (self.rx - self.origin_x) / self.resolution - 0.5
        py_map = (self.ry - self.origin_y) / self.resolution - 0.5

        px_rot = (map_w - 1) - py_map
        py_rot = (map_h - 1) - px_map

        sx = scaled.width() / map_w
        sy = scaled.height() / map_h

        px = x + px_rot * sx
        py = y + py_rot * sy

        arrow = QPolygonF([
            QPointF(0, -10),
            QPointF(6, 8),
            QPointF(-6, 8)
        ])

        painter.save()
        painter.translate(px, py)
        painter.rotate(-self.yaw)
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(arrow)
        painter.restore()



# ---------------------- Telemetry Text -------------------------

class TelemetryWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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

        # ICON BUTTON ROW
        icon_row = QHBoxLayout()
        icon_row.setSpacing(16)

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

        # TEXT FIELD
        self.textbox = QLineEdit()
        self.textbox.setPlaceholderText("Enter projection message...")
        self.textbox.setFixedHeight(42)
        self.textbox.setObjectName("ProjectionText")

        # SHOW & CLEAR BUTTONS
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

        layout.addLayout(icon_row)
        layout.addWidget(self.textbox)
        layout.addLayout(buttons)


# ---------------------- Joystick ---------------------------

class JoystickWidget(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # SPEAKER + TALK
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

        # THROTTLE
        throttle_label = QLabel("Throttle")
        layout.addWidget(throttle_label)

        slider = QSlider(Qt.Horizontal)
        slider.valueChanged.connect(lambda v: print("[THROTTLE]", v))
        layout.addWidget(slider)

        # JOYSTICK PAD
        pad = QFrame()
        pad.setObjectName("JoystickPad")
        pad.setFixedSize(240, 240)
        pad.setStyleSheet("background-color: #A7C8E8; border-radius: 120px;")
        container = QWidget(pad)
        container.setGeometry(0, 0, 240, 240)

        # helper for circular buttons
        def make_button(icon_file, cmd):
            b = QToolButton(container)
            b.setObjectName("JoyBtn")
            b.setIcon(QIcon(icon_file))
            b.setIconSize(QSize(32, 32))
            b.setFixedSize(56, 56)
            b.setAutoRaise(False)
            b.setCheckable(False)

            # Press & hold (using signals)
            b.pressed.connect(lambda c=cmd: self.callback(c))
            b.released.connect(lambda: self.callback("stop"))

            b.setStyleSheet("""
                QToolButton#JoyBtn {
                    background: white;
                    border-radius: 28px;
                }
                QToolButton#JoyBtn:hover {
                    background: #f0f0f0;
                }
            """)
            return b

        # Create buttons
        up_btn = make_button("icons/up.png", "up")
        down_btn = make_button("icons/down.png", "down")
        left_btn = make_button("icons/left.png", "left")
        right_btn = make_button("icons/right.png", "right")

        # CENTER STOP BUTTON
        center_btn = QToolButton(container)
        center_btn.setObjectName("JoyCenter")
        center_btn.setIcon(QIcon("icons/stop.png"))
        center_btn.setIconSize(QSize(36, 36))
        center_btn.setFixedSize(70, 70)
        center_btn.setAutoRaise(False)
        center_btn.setCheckable(False)

        center_btn.pressed.connect(lambda: self.callback("stop"))
        center_btn.released.connect(lambda: self.callback("stop"))

        center_btn.setStyleSheet("""
            QToolButton#JoyCenter {
                background: #E34F4F;
                border-radius: 35px;
            }
            QToolButton#JoyCenter:hover {
                background: #D13C3C;
            }
        """)

        # POSITION BUTTONS MANUALLY
        center_btn.move(120 - 35, 120 - 35)

        up_btn.move(120 - 28, 40 - 28)
        down_btn.move(120 - 28, 200 - 28)
        left_btn.move(40 - 28, 120 - 28)
        right_btn.move(200 - 28, 120 - 28)

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

        # Telemetry backend (rosbridge)
        from telemetry import Telemetry
        self.telemetry = Telemetry()
        self._map_loaded_from_telemetry = False

        # Poll telemetry in GUI thread
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.refresh_telemetry_from_ros)
        self.telemetry_timer.start(100)   # every 100 ms

        # TELEOP STATE
        self.current_cmd = "stop"

        # TELEOP TIMER (starts only while holding a button)
        self.teleop_timer = QTimer(self)
        self.teleop_timer.timeout.connect(self.publish_continuous_cmd)

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

        self.map_widget = MapViewWidget()
        map_layout.addWidget(self.map_widget)

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

    # ---------------- Telemetry polling in GUI thread ----------------

    def refresh_telemetry_from_ros(self):

        # map load
        # if not self._map_loaded_from_telemetry:
        #     map_info, map_data = self.telemetry.get_map()
        #     if map_info is not None:
        #         print("[Main] Loading map now...")
        #         self.map_widget.load_from_occupancy(map_info, map_data)
        #         self._map_loaded_from_telemetry = True


        if not self._map_loaded_from_telemetry:
            # Update status in map card
            if not self.telemetry.ros.is_connected:
                self.map_widget.set_status("Connecting to ROS…")
                return

            map_info, map_data = self.telemetry.get_map()

            if map_info is None:
                self.map_widget.set_status("Waiting for /map…")
                return

            # Map arrived!
            self.map_widget.set_status("Map received, rendering…")
            print("[Main] Loading map now...")
            self.map_widget.load_from_occupancy(map_info, map_data)
            self._map_loaded_from_telemetry = True


        # pose update
        pose = self.telemetry.get_pose()
        if pose:
            x, y, yaw, speed = pose
            self.map_widget.update_robot_pose(x, y, yaw)

            tele = self.findChild(TelemetryWidget)
            if tele:
                tele.text.setText(
                    f"X: {x:.2f}\nY: {y:.2f}\nYaw: {yaw:.1f}°\nSpeed: {speed:.2f}"
                )


    # ---------------- TELEOP LOGIC --------------------

    def handle_teleop(self, cmd):
        self.current_cmd = cmd

        if cmd == "stop":
            # Stop continuous publishing and send one stop
            self.teleop_timer.stop()
            send_cmd_vel(0.0, 0.0)
        else:
            # Start continuous publishing only while a button is held
            if not self.teleop_timer.isActive():
                self.teleop_timer.start(50)  # 20 Hz

    def publish_continuous_cmd(self):
        linear_speed = 0.30
        angular_speed = 1.0

        if self.current_cmd == "up":
            send_cmd_vel(linear_speed, 0.0)
        elif self.current_cmd == "down":
            send_cmd_vel(-linear_speed, 0.0)
        elif self.current_cmd == "left":
            send_cmd_vel(0.0, angular_speed)
        elif self.current_cmd == "right":
            send_cmd_vel(0.0, -angular_speed)
        else:
            # Safety: ensure we don't drift
            send_cmd_vel(0.0, 0.0)

    # ---------------- STYLES --------------------

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
