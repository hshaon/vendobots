# ROS Workspace
```main_interface.py``` running in the ```base_station``` commuincates with the robot via ROS bridge. So in the robot side, ROS bridge must be installed and kept running.

### Run the following commands to install ROS Bridge on Delivery Robot (Ubuntu 20.04)
$ sudo apt update
$ sudo apt install ros-noetic-rosbridge-suite

### Start rosbridge on websocket [Keep it running]
$ roslaunch rosbridge_server rosbridge_websocket.launch
