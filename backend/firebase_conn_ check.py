from dronekit import connect, VehicleMode, LocationGlobalRelative
import firebase_admin
from firebase_admin import credentials, db
import time
import threading

# Connect to the drone
vehicle = connect('COM4', wait_ready=True, baud=57600)
print("Connected to Pixhawk")

#open camera

# Firebase setup
cred = credentials.Certificate("C:\\Users\\barat\\OneDrive\\Desktop\\dronedeliverysystem\\backend\\serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://delivery-drone-24f45-default-rtdb.firebaseio.com/'
})
print("Firebase initialized successfully")

gps_ref = db.reference('drone_location')  # Corrected path
mission_status_ref = db.reference('mission/status')  # Mission status path

# Set initial status to "Idle" when the script starts
mission_status_ref.set("Idle")

# Function to update GPS coordinates in Firebase
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

def wait_for_mission_data():
    print("Waiting for mission data from Firebase...")
    mission_ref = db.reference('mission')
    while True:
        mission_data = mission_ref.get()
        if mission_data and 'latitude' in mission_data and 'longitude' in mission_data:
            print("Mission Data Received!")
            print(f"Target Location: ({mission_data['latitude']}, {mission_data['longitude']})")
            return mission_data
        time.sleep(2)

def wait_for_mission_start():
    print("Waiting for mission deployment...")
    while True:
        status = mission_status_ref.get()
        if status == "Deployed":
            print("🚀 Mission Started!")
            mission_status_ref.set("In Progress")  # Persist status
            return True
        time.sleep(2)

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
    print("Mode set to GUIDED")
    vehicle.armed = True
    while not vehicle.armed:
        print("Waiting for arming...")
        time.sleep(1)
    
    print("Taking off to 10 meters...")
    vehicle.simple_takeoff(1)
    
    while True:
        if vehicle.location.global_relative_frame.alt >= 9.5:
            print("Reached target altitude")
            break
        time.sleep(1)
    
    print(f"Flying to destination: {target_lat}, {target_lon}")
    mission_status_ref.set("Flying to Destination")
    destination = LocationGlobalRelative(target_lat, target_lon, 1)
    vehicle.simple_goto(destination)

    while True:
        distance = ((vehicle.location.global_frame.lat - target_lat)**2 +
                    (vehicle.location.global_frame.lon - target_lon)**2)**0.5 * 111000
        print(f"Distance to destination: {distance:.2f} meters")
        if distance < 5:
            print("Reached destination")
            mission_status_ref.set("Arrived at Destination")
            break
        time.sleep(2)

    
    print("Mission complete, returning to launch")
    mission_status_ref.set("Returning to Launch")
    vehicle.mode = VehicleMode("RTL")
    
    while vehicle.mode.name != "RTL":
        time.sleep(1)
    
    print("Drone landed, resetting mission status to Idle")
    mission_status_ref.set("Idle")  # Reset status on completion
except Exception as e:
    print(f"Mission error: {e}")
    mission_status_ref.set(f"Error: {str(e)}")
finally:
    while True:
        time.sleep(1)
