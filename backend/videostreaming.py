from flask import Flask, Response
import cv2
from picamera2 import Picamera2
import threading

app = Flask(__name__)

# Global variable to store the camera and streaming status
picam2 = None
streaming = False

def init_camera():
    global picam2
    picam2 = Picamera2()
    config = picam2.create_video_configuration()
    picam2.configure(config)
    picam2.start()

def generate_frames():
    global picam2, streaming
    try:
        while streaming:
            # Capture frame from Picamera2
            frame = picam2.capture_array()
            
            # Convert to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            
            if not ret:
                break
            
            # Convert to bytes for streaming
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except Exception as e:
        print(f"Error in frame generation: {e}")
    finally:
        if picam2:
            picam2.stop()

@app.route('/video_feed')
def video_feed():
    global streaming
    streaming = True
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask_server():
    app.run(host='0.0.0.0', port=5000)

def start_camera_stream():
    # Initialize camera
    init_camera()
    
    # Start Flask server in a separate thread
    threading.Thread(target=run_flask_server, daemon=True).start()

if __name__ == '__main__':
    start_camera_stream()