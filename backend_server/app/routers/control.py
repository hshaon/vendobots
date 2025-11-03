from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app import schemas
import cv2  # Imports OpenCV
import time

router = APIRouter(prefix="/control", tags=["control"])

# --- EXISTING COMMAND ENDPOINT ---
@router.post("/command", response_model=schemas.ControlResponse)
def send_robot_command(command: schemas.ControlCommand):
    valid_commands = {"forward", "backward", "left", "right", "stop"}
    
    if command.command.lower() not in valid_commands:
        return schemas.ControlResponse(
            status="error",
            message=f"Invalid command: {command.command}. Use one of: {', '.join(valid_commands)}"
        )

    print(f"Robot {command.robot_id} received command: {command.command.upper()}")

    return schemas.ControlResponse(
        status="success",
        message=f"Command '{command.command.upper()}' sent to Robot {command.robot_id}"
    )


# --- NEW LIVE VIDEO STREAMING ENDPOINT ---
def generate_frame():
    # Attempt to use DirectShow (DSHOW) backend for better stability on Windows.
    # If DSHOW fails, it defaults to the system's preferred backend.
    
    # NOTE: The index 0 is your primary camera. Use 1, 2, etc., if you have issues.
    camera = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
    
    # Wait briefly for the camera initialization to complete
    time.sleep(0.5)

    if not camera.isOpened():
        print("CRITICAL ERROR: Could not open camera. Check index or device availability.")
        # Yield an error message or stop the generator cleanly
        return

    try:
        while True:
            # 1. Read frame from camera
            success, frame = camera.read()
            if not success:
                print("Error: Failed to read frame from camera.")
                # Attempt to restart the camera capture or exit cleanly
                break
                
            # 2. Encode the frame as JPEG
            # Use 90 quality for good balance of speed and clarity
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ret:
                continue

            # 3. Yield the frame data formatted as Motion JPEG (MJPEG)
            frame_bytes = buffer.tobytes()
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )
            
            # Optional: Add a small sleep to limit frame rate (e.g., 30 FPS = 0.033s)
            time.sleep(0.01) # Reduced sleep for smoother video

    except Exception as e:
        print(f"Exception during frame generation: {e}")
    finally:
        # Important: Release the camera resources when done
        camera.release()
        print("Camera released.")


@router.get("/video_feed")
def video_feed():
    """
    Returns the video feed as a Motion JPEG stream.
    """
    return StreamingResponse(
        generate_frame(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
