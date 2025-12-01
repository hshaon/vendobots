# Vendobot Projection System — Raspberry Pi 5

This README describes how to set up and run the **Robot Intention Projection System** on a Raspberry Pi 5 using rosbridge, Pygame, and roslibpy.  
The projector displays **giant arrows on the floor**, predicting the robot’s intended turn *ahead of time* using the TEB local planner path.

---

# Overview

The system consists of:

- **Raspberry Pi 5** running:
  - Real-time Transport Protocol (RTP) for camera and ROS environment
  - A **projection application** (projection.py) running (Pygame fullscreen UI)
  - `roslibpy` to subscribe to robot navigation topics
- **Robot running ROS1** (Ubuntu 20.04)
  - Provides `/move_base/TebLocalPlannerROS/local_plan`
  - rosbridge server at port `9090`
- **Projector connected via HDMI** to Raspberry Pi 5

The Pi subscribes to the robot’s predicted local path and projects **LEFT**, **RIGHT**, **FORWARD**, or **STOP** arrows before the robot reaches intersections.

---

# Folder Structure

```
~/arrow_images/
    forward.png
    left.png
    right.png
    stop.png
~/Desktop/projection.py
```

---

# Installation Steps

## 1. Install system dependencies

```bash
sudo apt update
sudo apt install -y python3-pygame python3-pip
```

## 2. Install `roslibpy` system‑wide

```bash
pip3 install roslibpy --break-system-packages
```

If prompted for additional dependencies:

```bash
pip3 install cffi --break-system-packages
```

---

# Arrow Images

Place your projection icons here:

```
/home/pi/arrow_images/
```

Recommended resolution: **512×512** or **1024×1024** PNG.

Required filenames:

- `forward.png`
- `left.png`
- `right.png`
- `stop.png`

---

# Fullscreen Projection Script (`projection.py`)

This script:

- connects to rosbridge (`192.168.2.115:9090`)
- listens to `/move_base/TebLocalPlannerROS/local_plan`
- computes future turning intent
- displays giant fullscreen arrows
- exits on **ESC**, **Q**, or mouse click

Save as:

```
/home/pi/Desktop/projection.py
```

---

# Running the Projector App

```bash
python3 ~/Desktop/projection.py
```

Exit using:

- **ESC**
- **Q**
- **Mouse click**
- or **CTRL + C** in terminal

---

# Optional: Start Automatically on Boot (systemd)

Create:

```bash
sudo nano /etc/systemd/system/vendobot_projection.service
```

Paste:

```
[Unit]
Description=Vendobot Intention Projection
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Desktop/projection.py
Restart=always
User=pi
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vendobot_projection
sudo systemctl start vendobot_projection
```

---

# Debugging

### Test rosbridge connectivity:

```bash
curl http://192.168.2.115:9090
```

### Inspect local plan:

```bash
rostopic echo /move_base/TebLocalPlannerROS/local_plan -n 1
```

If nothing prints → robot navigation idle.

---

# License

MIT License © 2025 Vendobot Project

---

# Support

Open an issue or contact the development team for enhancements or bug reports.
