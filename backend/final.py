from dronekit import connect, VehicleMode, LocationGlobalRelative
import firebase_admin
from firebase_admin import credentials, db
import time
import threading
import cv2
import numpy as np
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from flask import Flask, Response

# Initialize Flask app
app = Flask(__name__)

# Servo motor setup
SERVO_PIN = 18  # GPIO pin for servo motor
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz PWM
servo.start(0)

# Connect to the drone
vehicle = connect('COM4', wait_ready=True, baud=57600)
print("Connected to Pixhawk")

# Camera setup
picam2 = Picamera2()
config = picam2.create_still_configuration()
picam2.configure(config)
picam2.start()

# Firebase setup
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://delivery-drone-24f45-default-rtdb.firebaseio.com/'
})
print("Firebase initialized successfully")

gps_ref = db.reference('drone_location')
mission_status_ref = db.reference('mission/status')
mission_status_ref.set("Idle")

# Start GPS updates in a separate thread
def update_gps():
    while True:
        try:
            if vehicle.location.global_frame.lat and vehicle.location.global_frame.lon:
                lat = vehicle.location.global_frame.lat
                lon = vehicle.location.global_frame.lon
                alt = vehicle.location.global_frame.alt
                
                gps_data = {
                    "latitude": lat, 
                    "longitude": lon, 
                    "altitude": alt,
                    "timestamp": int(time.time() * 1000)
                }
                gps_ref.set(gps_data)
                print(f"Updated GPS: {gps_data}")
            else:
                print("Waiting for GPS lock...")
        except Exception as e:
            print(f"Error updating GPS: {e}")
        
        time.sleep(1)

gps_thread = threading.Thread(target=update_gps, daemon=True)
gps_thread.start()

# Stream video to web app
def generate_frames():
    while True:
        picam2.capture_file("current_frame.jpg")
        frame = cv2.imread("current_frame.jpg")
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Main mission execution
mission_status_ref.set("Waiting for mission deployment")
while True:
    mission_data = mission_status_ref.get()
    if mission_data and mission_data != "Idle":
        break
    time.sleep(1)

target_lat = mission_data['latitude']
target_lon = mission_data['longitude']
#expected_qr = mission_data['expected_qr']

vehicle.mode = VehicleMode("GUIDED")
vehicle.armed = True
while not vehicle.armed:
    print("Ärming...")
    time.sleep(1)

vehicle.simple_takeoff(10)
while vehicle.location.global_relative_frame.alt < 9.5:
    time.sleep(1)

destination = LocationGlobalRelative(target_lat, target_lon, 10)
vehicle.simple_goto(destination)

while True:
    distance = ((vehicle.location.global_frame.lat - target_lat)**2 +
                (vehicle.location.global_frame.lon - target_lon)**2)**0.5 * 111000
    if distance < 5:
        break
    time.sleep(2)

vehicle.simple_goto(LocationGlobalRelative(target_lat, target_lon, 5))
time.sleep(5)

picam2.capture_file("current_frame.jpg")
image = cv2.imread("current_frame.jpg")
detector = cv2.QRCodeDetector()
data, bbox, _ = detector.detectAndDecode(image)

if data:
    mission_status_ref.set("Landing for Payload Release")
    vehicle.mode = VehicleMode("LAND")
    while vehicle.location.global_relative_frame.alt > 0.5:
        time.sleep(1)
    
    servo.ChangeDutyCycle(10)
    time.sleep(1)
    servo.ChangeDutyCycle(0)
    
    vehicle.simple_takeoff(10)
    while vehicle.location.global_relative_frame.alt < 9.5:
        time.sleep(1)
    
    vehicle.mode = VehicleMode("RTL")
    mission_status_ref.set("Returning to Launch")
else:
    mission_status_ref.set("QR Code Verification Failed")
    vehicle.mode = VehicleMode("RTL")

# Start Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
