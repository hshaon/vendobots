import roslibpy

ros = roslibpy.Ros(host='192.168.2.115', port=9090)

def on_ready():
    print("Connected to ROS via rosbridge!")

ros.on_ready(on_ready)
ros.run()

ros.terminate()
