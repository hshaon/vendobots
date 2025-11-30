# Raspberry Pi 5 --- ROS Noetic + Ultra‑Low‑Latency Camera Streaming

## Overview

-   Running **ROS Noetic inside Docker** on Raspberry Pi 5\
-   Streaming **ultra‑low‑latency RTP H.264 video** from a USB camera\
-   Auto‑starting the camera pipeline at boot\
-   Connecting the Pi to a **remote ROS master** on the robot\
-   Receiving the stream on a **base‑station Qt GUI**

------------------------------------------------------------------------

## Requirements

### Raspberry Pi 5

-   Raspberry Pi OS (Bookworm)
-   Docker installed
-   USB webcam (MJPEG capable)

### Base Station

-   Ubuntu 22.04 / 24.04
-   ROS master running on robot
-   GStreamer installed

------------------------------------------------------------------------

## Install Docker on Raspberry Pi 5

``` bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo reboot
```

Verify Docker:

``` bash
docker --version
docker run hello-world
```

------------------------------------------------------------------------

## Pull ROS Noetic Image

``` bash
docker pull ros:noetic-ros-base
```

------------------------------------------------------------------------

## Create ROS Noetic Container

``` bash
docker run -it --name ros1_noetic --network host ros:noetic-ros-base bash
```

### Start & attach to container (after reboot)

``` bash
docker start ros1_noetic
docker exec -it ros1_noetic bash
```

------------------------------------------------------------------------

## Configure ROS Environment (inside container)

``` bash
echo "export ROS_MASTER_URI=http://<ROBOT_IP>:11311" >> ~/.bashrc
echo "export ROS_HOSTNAME=<PI_IP>" >> ~/.bashrc
echo "export ROS_IP=<PI_IP>" >> ~/.bashrc
source ~/.bashrc
```

Test:

``` bash
rosnode list
```

------------------------------------------------------------------------

## Install GStreamer for Camera Streaming

``` bash
sudo apt update
sudo apt install -y   gstreamer1.0-tools   gstreamer1.0-libav   gstreamer1.0-plugins-good   gstreamer1.0-plugins-bad   gstreamer1.0-plugins-ugly   v4l-utils
```

------------------------------------------------------------------------

## Check Camera Support

``` bash
ls /dev/video*
v4l2-ctl -d /dev/video0 --list-formats-ext
```

Ensure MJPEG is present.

------------------------------------------------------------------------

## Start Ultra‑Low‑Latency RTP Stream (Pi → Base Station)

``` bash
gst-launch-1.0 -v   v4l2src device=/dev/video0 !   image/jpeg,width=640,height=480,framerate=30/1 !   jpegdec ! videoconvert !   openh264enc bitrate=3000000 complexity=0 rate-control=1 !   video/x-h264,profile=baseline !   h264parse config-interval=-1 !   rtph264pay pt=96 !   udpsink host=<BASE_STATION_IP> port=5000 sync=false async=false
```

🟢 Latency: **30--50 ms**\
🟢 Works perfectly with Qt/GStreamer GUI

------------------------------------------------------------------------

## Base‑Station Receiver (GStreamer)

Install:

``` bash
sudo apt update
sudo apt install -y   gstreamer1.0-tools gstreamer1.0-libav   gstreamer1.0-plugins-good gstreamer1.0-plugins-bad   gstreamer1.0-plugins-ugly
```

Test viewing the RTP stream:

``` bash
gst-launch-1.0 -v   udpsrc port=5000   caps="application/x-rtp, media=video, encoding-name=H264, payload=96" !   rtph264depay ! h264parse ! avdec_h264 ! videoconvert !   autovideosink sync=false
```

------------------------------------------------------------------------

## Auto‑Start Camera Streaming on Boot (systemd)

Create service:

``` bash
sudo nano /etc/systemd/system/rpi_cam.service
```

Paste:

    [Unit]
    Description=Ultra Low Latency Camera Stream (RTP H264)
    After=network-online.target

    [Service]
    ExecStart=/usr/bin/gst-launch-1.0 -v   v4l2src device=/dev/video0 !   image/jpeg,width=640,height=480,framerate=30/1 !   jpegdec ! videoconvert !   openh264enc bitrate=3000000 complexity=0 rate-control=1 !   video/x-h264,profile=baseline !   h264parse config-interval=-1 !   rtph264pay pt=96 !   udpsink host=<BASE_STATION_IP> port=5000 sync=false async=false

    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target

Enable:

``` bash
sudo systemctl daemon-reload
sudo systemctl enable rpi_cam.service
sudo systemctl start rpi_cam.service
```

------------------------------------------------------------------------

## Diagnostics

Check service:

``` bash
sudo systemctl status rpi_cam.service
```

Check logs:

``` bash
journalctl -u rpi_cam.service -f
```

------------------------------------------------------------------------

## License

MIT License unless otherwise specified.

------------------------------------------------------------------------

## Support

Open an Issue or request enhancements anytime.
