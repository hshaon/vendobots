import socketio

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('Connected!')

@sio.event
def connect_error(data):
    print('Connection failed:', data)

@sio.event
def disconnect():
    print('Disconnected!')

sio.connect('https://hricameratest.onrender.com/')
sio.wait()
