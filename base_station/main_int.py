import sys
from datetime import datetime

from PyQt5.QtGui import (
    QPixmap, QPainter, QColor, QIcon, QPolygonF,
    QTransform, QImage, QPainterPath
)
from PyQt5.QtCore import QSize, Qt, QTimer, QPointF, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QToolButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QSlider, QFrame,
    QLineEdit, QGraphicsDropShadowEffect, QSizePolicy,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)

from send_movement import init_connection, send_cmd_vel, stop_robot

# Database & robot config ------------------------
DB_HOST = "192.168.2.129"
DB_PORT = 5432
DB_NAME = "vendor_bot"
DB_USER = "postgres"
DB_PASSWORD = "102403"

ROBOT_ID = 1          # which robot_id this UI controls
ROBOT_IP = "192.168.2.115"  # IP of the robot's ROS bridge (for CLI send_goal if needed)

# Try to import psycopg2 (PostgreSQL)
try:
    import psycopg2
except ImportError:
    psycopg2 = None
    print("[Queue] WARNING: psycopg2 not installed. Delivery Queue will be disabled.")

# Try to import RosGoalSender for navigation goals
try:
    from send_goal import RosGoalSender
except ImportError:
    RosGoalSender = None
    print("[Queue] WARNING: send_goal.py (RosGoalSender) not found. Dispatch will only update DB, no nav goal will be sent.")


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
    new_frame = pyqtSignal(QImage)   # Qt-safe signal

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
        _ = bus.poll(self.Gst.MessageType.ANY, 0)

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
        # Rounded corners
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

        # Status Overlay
        self.status = QLabel("Connecting to ROS…")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("""
            font-size: 15px;
            color: #555;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.status)

    def set_status(self, text):
        self.status.setText(text)
        self.status.show()
        self.rotated_pixmap = None
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
                v = data[base + x]
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
        flip.scale(-1, 1)
        self.rotated_pixmap = pm.transformed(flip)

        self.resolution = map_info["resolution"]
        self.origin_x = map_info["origin"]["position"]["x"]
        self.origin_y = map_info["origin"]["position"]["y"]

        print("[Map] Ready, rotated size =", self.rotated_pixmap.size())

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
        #py_rot = px_map

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

            # Press & hold
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

        # Connect with ROS-Bridge (for teleop)
        init_connection()

        # Telemetry backend (rosbridge)
        from telemetry import Telemetry
        self.telemetry = Telemetry()
        self._last_nav_code = None

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

        # Goal sender for navigation dispatch (SHARED ROS CLIENT)
        self.goal_sender = None
        if RosGoalSender is not None:
            try:
                # Use the SAME Ros connection as telemetry to avoid Twisted conflicts
                self.goal_sender = RosGoalSender(ros=self.telemetry.ros)
                print("[Queue] RosGoalSender initialized with shared ROS connection.")
            except Exception as e:
                print(f"[Queue] ERROR initializing RosGoalSender: {e}")
                self.goal_sender = None
        else:
            print("[Queue] RosGoalSender not available; dispatch will only update DB.")

        # Database connection
        self.db_conn = None
        if psycopg2 is not None:
            try:
                self.db_conn = psycopg2.connect(
                    host=DB_HOST,
                    port=DB_PORT,
                    dbname=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD
                )
                self.db_conn.autocommit = True
                print("[Queue] Connected to PostgreSQL.")
            except Exception as e:
                print(f"[Queue] ERROR connecting to DB: {e}")
                self.db_conn = None
        else:
            print("[Queue] psycopg2 not installed; Delivery Queue disabled.")

        # ----------------- Root Layout with Tabs -----------------
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Tabs
        self.control_tab = QWidget()
        self.queue_tab = QWidget()
        self.logs_tab = QWidget()

        self.tabs.addTab(self.control_tab, "Control")
        self.tabs.addTab(self.queue_tab, "Delivery Queue")
        self.tabs.addTab(self.logs_tab, "Logs")

        # Build each tab
        self.build_control_tab()
        self.build_queue_tab()
        self.build_logs_tab()

        # Queue refresh timer (only if DB OK)
        if self.db_conn is not None:
            self.queue_refresh_timer = QTimer(self)
            self.queue_refresh_timer.timeout.connect(self.refresh_delivery_queue)
            self.queue_refresh_timer.start(2000)  # every 2 seconds
        else:
            self.queue_refresh_timer = None

    # ==========================================================
    # CONTROL TAB (Your existing UI moved here)
    # ==========================================================
    def build_control_tab(self):
        # LIVE FEED BLOCK
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

        # MAP BLOCK
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

        # TOP ROW
        top_row = QHBoxLayout()
        top_row.setSpacing(24)
        top_row.addLayout(live_container, 3)
        top_row.addLayout(map_container, 3)

        # TELEMETRY BLOCK
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

        # PROJECTION BLOCK
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

        # JOYSTICK
        joy = JoystickWidget(self.handle_teleop)

        # BOTTOM ROW
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(24)
        bottom_row.addLayout(tele_container, 2)
        bottom_row.addLayout(proj_container, 3)
        bottom_row.addWidget(joy, 3)

        # MAIN LAYOUT FOR CONTROL TAB
        main = QVBoxLayout(self.control_tab)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(24)
        main.addLayout(top_row, 3)
        main.addLayout(bottom_row, 3)

    # ==========================================================
    # DELIVERY QUEUE TAB
    # ==========================================================
    def build_queue_tab(self):
        layout = QVBoxLayout(self.queue_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Delivery Queue")
        header.setStyleSheet("font-size: 20px; font-weight: 600; color: #333;")
        layout.addWidget(header)

        # 1️⃣ CREATE TABLE FIRST
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels(
            ["Order ID", "Address", "Location", "Status", "Created At", "Actions"]
        )

        # Column sizes
        header_view = self.queue_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)           # Address
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)           # Location
        header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status
        header_view.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Created
        header_view.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Actions

        self.queue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.queue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.queue_table.setSelectionMode(QTableWidget.SingleSelection)

        layout.addWidget(self.queue_table)

        if self.db_conn is None:
            warn = QLabel("Database connection not available. Queue is disabled.")
            warn.setStyleSheet("color: #b00; font-size:14px;")
            layout.addWidget(warn)

    def refresh_delivery_queue(self):
        if self.db_conn is None:
            return

        try:
            cur = self.db_conn.cursor()
            cur.execute("""
                SELECT id, address, dest_pos_x, dest_pos_y, status, created_at
                FROM delivery_records
                WHERE robot_id = %s
                  AND status IN ('NEW','LOADING','READY','IN_PROGRESS')
                ORDER BY created_at ASC
            """, (ROBOT_ID,))
            rows = cur.fetchall()
            cur.close()
        except Exception as e:
            self.log(f"[Queue] Error fetching records: {e}")
            return

        self.queue_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            order_id, address, dest_x, dest_y, status, created_at = row

            # Column 0: ID
            self.queue_table.setItem(row_idx, 0, QTableWidgetItem(str(order_id)))

            # Column 1: Address
            self.queue_table.setItem(row_idx, 1, QTableWidgetItem(address or ""))

            # Column 2: Location (address preferred, else coords, else Unknown)
            if address and address.strip():
                loc_str = address.strip()
            else:
                try:
                    if dest_x is not None and dest_y is not None:
                        loc_str = f"{float(dest_x):.2f}, {float(dest_y):.2f}"
                    else:
                        loc_str = "Unknown"
                except Exception:
                    loc_str = "Unknown"
            self.queue_table.setItem(row_idx, 2, QTableWidgetItem(loc_str))

            # Column 3: Status
            self.queue_table.setItem(row_idx, 3, QTableWidgetItem(status or ""))

            # Column 4: Created datetime
            created_str = str(created_at) if created_at else ""
            self.queue_table.setItem(row_idx, 4, QTableWidgetItem(created_str))

            # Column 5: Actions
            actions_widget = QWidget()
            h = QHBoxLayout(actions_widget)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            h.addStretch()

            # Buttons depending on status
            if status == "NEW":
                btn_start = QPushButton("Start Loading")
                btn_start.setObjectName("QueueButton")
                btn_start.setFixedHeight(30)
                btn_start.clicked.connect(
                    lambda _, oid=order_id: self.set_order_status(oid, "LOADING")
                )
                h.addWidget(btn_start)

            elif status == "LOADING":
                btn_ready = QPushButton("Mark Loaded")
                btn_ready.setObjectName("QueueButton")
                btn_ready.setFixedHeight(30)
                btn_ready.clicked.connect(
                    lambda _, oid=order_id: self.set_order_status(oid, "READY")
                )
                h.addWidget(btn_ready)

            elif status == "READY":
                btn_dispatch = QPushButton("Dispatch")
                btn_dispatch.setObjectName("QueueButton")
                btn_dispatch.setFixedHeight(30)
                btn_dispatch.clicked.connect(
                    lambda _, oid=order_id, x=dest_x, y=dest_y: self.dispatch_order(oid, x, y)
                )
                h.addWidget(btn_dispatch)

            elif status == "IN_PROGRESS":
                btn_delivered = QPushButton("Mark Delivered")
                btn_delivered.setObjectName("QueueButton")
                btn_delivered.setFixedHeight(30)
                btn_delivered.clicked.connect(
                    lambda _, oid=order_id: self.set_order_status(oid, "DELIVERED")
                )
                h.addWidget(btn_delivered)

            h.addStretch()
            self.queue_table.setCellWidget(row_idx, 5, actions_widget)

    def set_order_status(self, order_id, new_status):
        if self.db_conn is None:
            QMessageBox.warning(self, "DB Error", "Database connection not available.")
            return

        try:
            cur = self.db_conn.cursor()
            cur.execute("""
                UPDATE delivery_records
                SET status = %s,
                    last_updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_status, order_id))
            cur.close()
            self.log(f"[Queue] Order {order_id} → {new_status}")
            self.refresh_delivery_queue()
        except Exception as e:
            self.log(f"[Queue] Error updating order {order_id} to {new_status}: {e}")
            QMessageBox.critical(self, "DB Error", str(e))

    def dispatch_order(self, order_id, dest_x, dest_y):
        if self.db_conn is None:
            QMessageBox.warning(self, "DB Error", "Database connection not available.")
            return

        # Check if robot already has an IN_PROGRESS job
        try:
            cur = self.db_conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM delivery_records
                WHERE robot_id = %s AND status = 'IN_PROGRESS'
            """, (ROBOT_ID,))
            (count,) = cur.fetchone()
            cur.close()
        except Exception as e:
            self.log(f"[Queue] Error checking active jobs: {e}")
            QMessageBox.critical(self, "DB Error", str(e))
            return

        if count > 0:
            QMessageBox.information(
                self,
                "Robot Busy",
                "Robot already has an active delivery (IN_PROGRESS)."
            )
            return

        # Convert dests to float to avoid Decimal JSON issues
        try:
            x = float(dest_x) if dest_x is not None else 0.0
            y = float(dest_y) if dest_y is not None else 0.0
        except Exception:
            x, y = 0.0, 0.0

        yaw_deg = 0.0  # simple default; you can calculate based on path if needed

        # Send goal via RosGoalSender (shared rosbridge)
        if self.goal_sender is not None:
            try:
                self.log(f"[Queue] Dispatching order {order_id} → x={x:.2f}, y={y:.2f}, yaw={yaw_deg:.1f}")
                self.goal_sender.send_goal(x, y, yaw_deg)
            except Exception as e:
                self.log(f"[Queue] ERROR dispatching goal for order {order_id}: {e}")
                QMessageBox.critical(self, "Dispatch Error", str(e))
                return
        else:
            self.log(f"[Queue] dispatch_order: RosGoalSender not available; only updating DB.")

        # Update order status to IN_PROGRESS
        try:
            cur = self.db_conn.cursor()
            cur.execute("""
                UPDATE delivery_records
                SET status = 'IN_PROGRESS',
                    last_updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (order_id,))
            cur.close()
            self.refresh_delivery_queue()
        except Exception as e:
            self.log(f"[Queue] Error setting order {order_id} to IN_PROGRESS: {e}")
            QMessageBox.critical(self, "DB Error", str(e))

    # ==========================================================
    # LOGS TAB
    # ==========================================================
    def build_logs_tab(self):
        layout = QVBoxLayout(self.logs_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("System Logs")
        header.setStyleSheet("font-size: 20px; font-weight: 600; color: #333;")
        layout.addWidget(header)

        self.logs_output = QTextEdit()
        self.logs_output.setReadOnly(True)
        self.logs_output.setStyleSheet("""
            QTextEdit {
                background: #F7F8FA;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.logs_output)

    def log(self, text):
        """Append a line to the Logs tab."""
        if hasattr(self, "logs_output") and self.logs_output is not None:
            ts = datetime.now().strftime("%H:%M:%S")
            self.logs_output.append(f"[{ts}] {text}")
        else:
            print(text)

    # ==========================================================
    # TELEMETRY polling in GUI thread
    # ==========================================================
    def refresh_telemetry_from_ros(self):
        # Map load
        if not self._map_loaded_from_telemetry:
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

        # Pose update
        pose = self.telemetry.get_pose()
        if pose:
            x, y, yaw, speed = pose
            self.map_widget.update_robot_pose(x, y, yaw)

            tele = self.findChild(TelemetryWidget)
            if tele:
                tele.text.setText(
                    f"X: {x:.2f}\nY: {y:.1f}°\nYaw: {yaw:.1f}°\nSpeed: {speed:.2f}"
                )
        
        self.check_navigation_status()



    def check_navigation_status(self):
        msg = self.telemetry.get_nav_status()
        if not msg:
            return

        status_list = msg.get("status_list", [])
        if not status_list:
            return

        last = status_list[-1]
        code = last.get("status", -1)
        text = last.get("text", "")

        # Only react if the status code CHANGED
        if code == self._last_nav_code:
            return

        self._last_nav_code = code   # Update state

        # ACTIVE
        if code == 1:
            self.log("[Nav] Robot is navigating to the target...")

        # SUCCEEDED
        elif code == 3:
            self.log("[Nav] Robot reached its goal!")
            self.auto_mark_delivered()

        # FAILED
        elif code in (4, 5):
            self.log(f"[Nav] Navigation failed: {text}")
            #self.auto_mark_failed()


    
    def auto_mark_delivered(self):
        if not self.db_conn:
            return

        cur = self.db_conn.cursor()
        cur.execute("""
            UPDATE delivery_records
            SET status='DELIVERED',
                last_updated_at = CURRENT_TIMESTAMP
            WHERE status='IN_PROGRESS' AND robot_id=%s
        """, (ROBOT_ID,))
        cur.close()

        self.refresh_delivery_queue()
        self.log("[Queue] Active delivery marked as DELIVERED.")


    def auto_mark_failed(self):
        if not self.db_conn:
            return

        cur = self.db_conn.cursor()
        cur.execute("""
            UPDATE delivery_records
            SET status='FAILED',
                last_updated_at = CURRENT_TIMESTAMP
            WHERE status='FAILED' AND robot_id=%s
        """, (ROBOT_ID,))
        cur.close()

        self.refresh_delivery_queue()
        self.log("[Queue] Active delivery marked as FAILED.")



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

        #QueueButton {
            padding: 2px 12px;
            border-radius: 5px;
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
