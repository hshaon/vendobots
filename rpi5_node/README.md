# Raspberry Pi 5 Camera Streaming Node (Ultra‑Low‑Latency RTP H.264)

Installation and setup instructions for enabling an ultra‑low‑latency video stream from a Raspberry Pi 5 to remote base‑station using GStreamer and RTP (H.264).

---

## 1. System Requirements

### Raspberry Pi
- Raspberry Pi 5  
- Raspberry Pi OS (Bookworm)  
- USB webcam supporting MJPEG (most cameras do)  

### Base Station (Receiver)
- Ubuntu 22.04 / 24.04 recommended  
- GStreamer installed  

---

## 2. Install Required Packages (Raspberry Pi)

Update the system and install required GStreamer components:

```bash
sudo apt update
sudo apt install -y     gstreamer1.0-tools     gstreamer1.0-libav     gstreamer1.0-plugins-good     gstreamer1.0-plugins-bad     gstreamer1.0-plugins-ugly     v4l-utils
```

These plugins include:
- `jpegdec` for MJPEG decoding  
- `openh264enc` for H.264 encoding  
- `rtph264pay` for RTP packetization  

---

## 3. Verify USB Camera Detection

List available video devices:

```bash
ls /dev/video*
```

Typical output contains `/dev/video0` for the USB camera.

List supported formats:

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

Ensure the camera lists at least:

- `MJPG` (preferred)
- `YUYV` (fallback)

If MJPEG is available, it will deliver the best performance.

---

## 4. Test Camera Functionality (Optional)

To test basic capture:

```bash
gst-launch-1.0 -v v4l2src device=/dev/video0 !     image/jpeg,width=640,height=480,framerate=30/1 !     jpegdec ! autovideosink
```

A preview window should open if a display is attached.  
If using SSH without display, skip this step.

---

## 5. Start the Ultra‑Low‑Latency RTP H.264 Video Stream (Raspberry Pi)

The pipeline below provides a highly optimized MJPEG → H.264 → RTP video stream using GStreamer:

```bash
gst-launch-1.0 -v   v4l2src device=/dev/video0 !   image/jpeg,width=640,height=480,framerate=30/1 !   jpegdec !   videoconvert !   openh264enc bitrate=3000000 complexity=0 rate-control=1 !   video/x-h264,profile=baseline !   h264parse config-interval=-1 !   rtph264pay pt=96 !   udpsink host=<BASE_STATION_IP> port=5000 sync=false async=false
```

Replace `<BASE_STATION_IP>` with the IP address of the machine receiving the stream.

Recommended settings:
- Resolution: 640×480  
- Framerate: 30 FPS  
- Bitrate: 3 Mbps  
- Low‑complexity encoder mode for minimal latency  

Latency is typically below 50 ms.

---

## 6. Install GStreamer on Base Station (Receiver)

On the receiving machine:

```bash
sudo apt update
sudo apt install -y     gstreamer1.0-tools     gstreamer1.0-libav     gstreamer1.0-plugins-good     gstreamer1.0-plugins-bad     gstreamer1.0-plugins-ugly
```

---

## 7. Test the Stream (Base Station)

Run the following GStreamer pipeline:

```bash
gst-launch-1.0 -v   udpsrc port=5000     caps="application/x-rtp, media=video, encoding-name=H264, payload=96" !   rtph264depay !   h264parse !   avdec_h264 !   videoconvert !   autovideosink sync=false
```

You should see the video stream with very low latency.

## 8. Auto-Start Stream on Boot (systemd)

Create a service:

``` bash
sudo nano /etc/systemd/system/rpi_cam.service
```

Paste:

    [Unit]
    Description=Ultra Low Latency Camera Stream (RTP H264)
    After=network-online.target

    [Service]
    ExecStart=/usr/bin/gst-launch-1.0 -v \
      v4l2src device=/dev/video0 ! \
      image/jpeg,width=640,height=480,framerate=30/1 ! \
      jpegdec ! \
      videoconvert ! \
      openh264enc bitrate=3000000 complexity=0 rate-control=1 ! \
      video/x-h264,profile=baseline ! \
      h264parse config-interval=-1 ! \
      rtph264pay pt=96 ! \
      udpsink host=<BASE_STATION_IP> port=5000 sync=false async=false

    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target

Enable it:

``` bash
sudo systemctl daemon-reload
sudo systemctl enable rpi_cam.service
sudo systemctl start rpi_cam.service
```


