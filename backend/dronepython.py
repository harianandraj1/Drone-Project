from dronekit import connect, VehicleMode, LocationGlobalRelative
import firebase_admin
from firebase_admin import credentials, db
import time

# Connect to Pixhawk
#vehicle = connect('COM4', wait_ready=True, baud=57600)

# Firebase setup
cred = credentials.Certificate("C:\\Users\\barat\\OneDrive\\Desktop\\dronedeliverysystem\\backend\\serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://delivery-drone-24f45-default-rtdb.firebaseio.com/'
})
print("Firebase initialized successfully")

# Firebase references
#gps_ref = db.reference('drone/gps')
target_location_lat = db.reference('mission/latitude')
target_location_lon = db.reference('mission/longitude')
expected_qr_ref = db.reference('mission/expected_qr')
deploy_ref = db.reference('mission/status')  # Deploy button status

def get_firebase_value(ref):
    """Safely retrieves a value from Firebase."""
    try:
        return ref.get()
    except Exception as e:
        print(f"Error reading from Firebase: {e}")
        return None

# Function to update drone's GPS to Firebase
#def update_gps():
    #while True:
        #if vehicle.location.global_frame.lat and vehicle.location.global_frame.lon:
           # lat = vehicle.location.global_frame.lat
           # lon = vehicle.location.global_frame.lon
           # alt = vehicle.location.global_frame.alt

           # gps_data = {"latitude": lat, "longitude": lon, "altitude": alt}
           # gps_ref.set(gps_data)  # Update GPS in Firebase
          #  print(f"Updated GPS: {gps_data}")

       # time.sleep(1)  # Update every second

# Function to wait for new mission data
def wait_for_new_mission_data():
    """Waits for new mission data from Firebase and returns it when the deploy button is clicked."""
    print("Waiting for new mission data from Firebase...")
    last_lat, last_lon, last_qr = None, None, None  # Store last received data
    
    while True:
        deploy_status = get_firebase_value(deploy_ref)
        
        print(f"Deploy status: {deploy_status}")  # Debugging line
        time.sleep(10)
    
        if deploy_status == "deployed":  # Deploy button clicked
            latitude = get_firebase_value(target_location_lat)
            longitude = get_firebase_value(target_location_lon)
            expected_qr = get_firebase_value(expected_qr_ref)
            
            if None not in (latitude, longitude, expected_qr):  # Ensure valid data
                if (latitude, longitude, expected_qr) != (last_lat, last_lon, last_qr):
                    print("New Mission Data Received!")
                    print(f"Target Location: {(latitude, longitude)}")
                    print(f"Expected QR Code: {expected_qr}")
                    
                    # Update last received values
                    last_lat, last_lon, last_qr = latitude, longitude, expected_qr
                    
                    # Reset deploy button to avoid reusing old data
                    deploy_ref.set("waiting")
                    return (latitude, longitude), expected_qr
        
        time.sleep(2)  # Avoid excessive Firebase reads

# Wait for new mission data
target_location, expected_qr = wait_for_new_mission_data()

# Start GPS updates in a separate thread
import threading
#gps_thread = threading.Thread(target=update_gps, daemon=True)
#gps_thread.start()



# Set drone to GUIDED mode and take off
#vehicle.mode = VehicleMode("GUIDED")
#vehicle.armed = True
#while not vehicle.armed:
   # print("Waiting for arming...")
   # time.sleep(1)

#print("Taking off to 10 meters...")
#vehicle.simple_takeoff(10)
