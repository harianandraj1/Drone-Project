from dronekit import connect, VehicleMode, LocationGlobalRelative
import firebase_admin
from firebase_admin import credentials, db
import time
import threading
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar

# Drone Control Constants
LANDING_PRECISION_THRESHOLD = 10  # Pixels from center
FRAME_CENTER_X = 320  # Assuming 640x480 resolution
FRAME_CENTER_Y = 240
MAX_CORRECTION_ANGLE = 5  # Maximum correction angle in degrees
DESCENT_RATE = 0.5  # Meters per second for controlled descent

# Connect to the drone
vehicle = connect('COM4', wait_ready=True, baud=57600)
print("Connected to Pixhawk")

# Firebase setup
cred = credentials.Certificate("/path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://delivery-drone-24f45-default-rtdb.firebaseio.com/'
})
print("Firebase initialized successfully")

# Firebase References
gps_ref = db.reference('drone_location')
mission_status_ref = db.reference('mission/status')
camera_feed_ref = db.reference('camera_feed')

# Set initial status to "Idle"
mission_status_ref.set("Idle")

def capture_qr_code():
    """ Capture frame from laptop webcam and detect QR codes """
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame")
            continue

        qr_codes = pyzbar.decode(frame)
        for qr in qr_codes:
            qr_data = qr.data.decode('utf-8')
            print(f"Detected QR Code: {qr_data}")
            cap.release()
            cv2.destroyAllWindows()
            return qr_data

        cv2.imshow("QR Code Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

def adaptive_precise_landing(expected_qr):
    """ Adaptive precise landing with QR code detection from laptop webcam """
    try:
        for attempt in range(5):
            detected_qr = capture_qr_code()
            if detected_qr == expected_qr:
                print("QR Code matched! Landing initiated.")
                vehicle.mode = VehicleMode("LAND")
                return True
            print(f"Landing attempt {attempt + 1}/5 failed. Retrying...")
            time.sleep(1)
        return False
    except Exception as e:
        print(f"Landing error: {e}")
        return False

def main_mission():
    try:
        print("Starting mission...")
        mission_data = db.reference('mission').get()
        target_lat = mission_data['latitude']
        target_lon = mission_data['longitude']
        expected_qr = mission_data['expected_qr']

        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
        while not vehicle.armed:
            time.sleep(1)
        
        vehicle.simple_takeoff(10)
        while vehicle.location.global_relative_frame.alt < 9.5:
            time.sleep(1)

        print(f"Flying to {target_lat}, {target_lon}")
        vehicle.simple_goto(LocationGlobalRelative(target_lat, target_lon, 10))
        time.sleep(10)

        print("Attempting precise landing with QR scanning")
        landing_success = adaptive_precise_landing(expected_qr)

        if landing_success:
            print("Payload delivered. Returning home.")
            vehicle.mode = VehicleMode("RTL")
        else:
            print("Landing failed.")

    except Exception as e:
        print(f"Mission error: {e}")
    finally:
        vehicle.close()

if __name__ == "__main__":
    main_mission()
