import cv2
import socket
import numpy as np
import time
import os
import threading
import socketio
from dotenv import load_dotenv
from datetime import datetime
#from EmotionEvaluation import satisficationEvaluation
import requests
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

#===============setup Saving Folder===============
current_folder = os.path.dirname(os.path.abspath(__file__))
record_folder = os.path.join(current_folder, "transaction_records")
current_video_file = None

recording = False
out = None
statusRecording = None

load_dotenv()

robot_id = os.getenv("ID_ROBOT")
backend_url = os.getenv("BE_URL")
control_camera_url = os.getenv("CONTROL_CAMERA_URL")
fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
save_path = ""
videourl = None

#=============== RECORD FUNCTIONS ===============

def start_record(fps, width, height):
    global out, recording, save_path

    save_path = os.path.join(
        record_folder,
        f"{current_video_file.replace(' ','_').replace(':','_').replace('-','_')}.mp4"
    )

    print("➡ Creating VideoWriter:", save_path)

    out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

    if not out.isOpened():
        print("❌ Error: VideoWriter failed to open")
    else:
        print("🎥 Recording started!")

    recording = True


def stop_record():
    global out, recording, statusRecording, videourl

    print("🛑 Stopping recording...")

    if out:
        out.release()
        out = None

        if videourl != 'NONE':
            send_videourl = videourl + "," + save_path
            url = f"{backend_url}/deliveryRecord/updateVideoURL"
            data = {"video_url": send_videourl}

            try:
                response = requests.post(url, json=data)
                response.raise_for_status()
                print("Video URL sent successfully.")

                #thread = threading.Thread(target=satisficationEvaluation, args=(save_path,), daemon=True)
                #thread.start()

            except Exception as e:
                print("Failed to send video URL:", e)

    recording = False
    statusRecording = None
    print("Recording stopped.")


#=============== GSTREAMER VIDEO RECEIVER ===============

class VideoStreamer:
    def __init__(self):
        Gst.init(None)
        self.pipeline = None
        self.appsink = None
        self.width = 0
        self.height = 0
        self.fps = 30  # default fallback

        pipeline_str = (
            "udpsrc port=5000 caps=\"application/x-rtp, media=video, encoding-name=H264, payload=96\" ! "
            "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! "
            "video/x-raw,format=RGB ! appsink name=appsink emit-signals=true sync=false max-buffers=1 drop=true"
        )

        self.pipeline = Gst.parse_launch(pipeline_str)
        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.connect("new-sample", self.on_new_sample)

    def start(self):
        print("📡 Starting GStreamer pipeline...")
        self.pipeline.set_state(Gst.State.PLAYING)

        # Run GLib main loop in background
        thread = threading.Thread(target=self.mainloop, daemon=True)
        thread.start()

    def mainloop(self):
        loop = GLib.MainLoop()
        loop.run()

    # ------------ Receive frame from appsink -------------
    def on_new_sample(self, sink):
        global recording, out

        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        caps = sample.get_caps()

        # width/height from GStreamer
        self.width = caps.get_structure(0).get_value("width")
        self.height = caps.get_structure(0).get_value("height")

        success, mapinfo = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR

        frame = np.frombuffer(mapinfo.data, dtype=np.uint8)
        frame = frame.reshape((self.height, self.width, 3))
        buf.unmap(mapinfo)

        # ---------- RECORDING ----------
        if recording and out:
            bgr = frame[:, :, ::-1]  # RGB → BGR
            out.write(bgr)

        return Gst.FlowReturn.OK


#=============== SOCKET.IO ===============

sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to server")
    sio.emit("join", {"room": robot_id})


@sio.event
def disconnect():
    print("❌ Disconnected from server")


@sio.on('camera_action')
def on_camera_action(data):
    global current_video_file, videourl, statusRecording, recording

    action = data.get('action')
    receivedVideoUrl = data.get('videourl')

    if action == "start":
        num_files = len(os.listdir(record_folder))
        now = datetime.now().replace(microsecond=0)
        current_video_file = f"transaction{num_files + 1}_{now}"

    videourl = receivedVideoUrl
    statusRecording = action

    print(f"📩 camera_action → {action}, videourl={videourl}")

    # Trigger recording
    if action == "start":
        if not recording:
            start_record(30, video_streamer.width, video_streamer.height)

    elif action == "stop":
        if recording:
            stop_record()


def start_socketio():
    print("Connecting to socket:", control_camera_url)
    try:
        sio.connect(control_camera_url, transports=['websocket'])
        sio.wait()
    except Exception as e:
        print("Socket.IO Error:", e)


#=============== MAIN START ===============

if __name__ == '__main__':
    # Start socket.io
    sio_thread = threading.Thread(target=start_socketio, daemon=True)
    sio_thread.start()

    # Start GStreamer receiver
    video_streamer = VideoStreamer()
    video_streamer.start()

    print("🚀 System running... (receiving frames + waiting for start/stop commands)")

    while True:
        time.sleep(1)
