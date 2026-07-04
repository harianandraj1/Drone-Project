from dronekit import connect, VehicleMode, LocationGlobalRelative
import firebase_admin
from firebase_admin import credentials, db
import time
import threading
import cv2
import numpy as np
from picamera2 import Picamera2
import RPi.GPIO as GPIO

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

# Start GPS updates in a separate thread
gps_thread = threading.Thread(target=update_gps, daemon=True)
gps_thread.start()

def detect_qr_code():
    """
    Detect QR code in the camera frame
    Returns QR code data or None if not detected
    """
    # Capture image
    picam2.capture_file("current_frame.jpg")
    
    # Read the captured image
    image = cv2.imread("current_frame.jpg")
    
    # Create QR code detector
    detector = cv2.QRCodeDetector()
    
    # Detect and decode QR code
    data, bbox, _ = detector.detectAndDecode(image)
    
    return data if data else None

def search_qr_code():
    """
    Search for QR code by making small drone movements
    """
    # List of movement patterns to search for QR code
    search_patterns = [
        (0, 0.5),   # slight right movement
        (0, -0.5),  # slight left movement
        (0.5, 0),   # slight forward movement
        (-0.5, 0)   # slight backward movement
    ]
    
    for dx, dy in search_patterns:
        # Small position adjustment
        current_location = vehicle.location.global_frame
        new_location = LocationGlobalRelative(
            current_location.lat + dx/111000,  # convert to lat/lon
            current_location.lon + dy/111000,
            current_location.alt
        )
        vehicle.simple_goto(new_location)
        time.sleep(2)  # Wait for movement to complete
        
        # Try to detect QR code
        qr_data = detect_qr_code()
        if qr_data:
            return qr_data
    
    return None

def release_payload():
    """
    Release payload using servo motor
    """
    # Rotate servo to release position
    servo.ChangeDutyCycle(10)  # Adjust angle as needed
    time.sleep(1)
    servo.ChangeDutyCycle(0)  # Stop PWM

def main_mission():
    try:
        # Wait for mission deployment
        wait_for_mission_start()

        # Fetch mission data
        mission_data = wait_for_mission_data()
        target_lat = mission_data['latitude']
        target_lon = mission_data['longitude']
        expected_qr = mission_data['expected_qr']
        
        # Set drone mode and takeoff
        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
        while not vehicle.armed:
            time.sleep(1)
        
        # Takeoff to 10 meters
        vehicle.simple_takeoff(10)
        while vehicle.location.global_relative_frame.alt < 9.5:
            time.sleep(1)
        
        # Fly to destination
        destination = LocationGlobalRelative(target_lat, target_lon, 10)
        vehicle.simple_goto(destination)

        # Wait until close to destination
        while True:
            distance = ((vehicle.location.global_frame.lat - target_lat)**2 +
                        (vehicle.location.global_frame.lon - target_lon)**2)**0.5 * 111000
            if distance < 5:
                break
            time.sleep(2)
        
        # Descend to lower altitude for QR code detection
        vehicle.simple_goto(LocationGlobalRelative(target_lat, target_lon, 5))
        time.sleep(5)  # Wait to stabilize
        
        # Attempt QR code detection
        qr_data = detect_qr_code()
        
        # If QR code not detected, search with small movements
        if not qr_data:
            qr_data = search_qr_code()
        
        # Verify QR code
        if qr_data == expected_qr:
            # Land and release payload
            mission_status_ref.set("Landing for Payload Release")
            vehicle.mode = VehicleMode("LAND")
            
            # Wait for landing
            while vehicle.location.global_relative_frame.alt > 0.5:
                time.sleep(1)
            
            # Release payload
            release_payload()
            
            # Takeoff again to 10 meters
            vehicle.simple_takeoff(10)
            while vehicle.location.global_relative_frame.alt < 9.5:
                time.sleep(1)
            
            # Return to launch
            vehicle.mode = VehicleMode("RTL")
            mission_status_ref.set("Returning to Launch")
        else:
            # QR code mismatch, return to launch
            mission_status_ref.set("QR Code Verification Failed")
            vehicle.mode = VehicleMode("RTL")
    
    except Exception as e:
        print(f"Mission error: {e}")
        mission_status_ref.set(f"Error: {str(e)}")
    finally:
        # Cleanup
        servo.stop()
        GPIO.cleanup()
        picam2.stop()

# Start the mission
if __name__ == "__main__":
    main_mission()