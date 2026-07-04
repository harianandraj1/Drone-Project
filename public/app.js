// Firebase Initialization
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getDatabase, ref, set, onValue } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-database.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCJv9n-4rlnQn-5yCm1MbHctuENJuEp7_Eg",
  authDomain: "delivery-drone-24f45.firebaseapp.com",
  databaseURL: "https://delivery-drone-24f45-default-rtdb.firebaseio.com",
  projectId: "delivery-drone-24f45",
  storageBucket: "delivery-drone-24f45.appspot.com",
  messagingSenderId: "190518067411",
  appId: "1:190518067411:web:9c37f54bede4c7df121426"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

// Function to deploy drone
function deployDrone() {
  console.log("deployDrone function called");
  
  const latitude = document.getElementById('latitude').value;
  const longitude = document.getElementById('longitude').value;
  const expectedQR = document.getElementById('expectedQR').value;
  
  console.log("Form values:", { latitude, longitude, expectedQR });

  if (latitude && longitude && expectedQR) {
    const missionData = {
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      expected_qr: expectedQR,
      status: 'Deployed',
      timestamp: Date.now()
    };
    
    console.log("Sending to Firebase:", missionData);
    
    set(ref(database, 'mission'), missionData)
      .then(() => {
        console.log("Firebase update successful");
        alert("🚀 Drone Deployed Successfully!");
      })
      .catch((error) => {
        console.error("Firebase update error:", error);
        alert("❌ Error deploying drone: " + error.message);
      });
  } else {
    console.log("Validation failed - missing fields");
    alert("⚠️ Please fill all fields before deploying.");
  }
}

// Function to switch between pages
function showPage(page) {
  console.log("Switching to page:", page);
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`${page}Page`).classList.add('active');
}

// Make functions available globally
window.deployDrone = deployDrone;
window.showPage = showPage;

// Real-time status listener (persisting last saved status)
const missionStatusRef = ref(database, 'mission/status');
onValue(missionStatusRef, (snapshot) => {
  const status = snapshot.val();
  if (status) {
    document.getElementById('status').innerText = status;
  }
});

// Initialize map
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM fully loaded");
  if (!document.getElementById('map')) return;

  console.log("Initializing map");
  try {
    var map = L.map('map').setView([10.9958668, 76.7702428], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    var droneIcon = L.icon({
      iconUrl: 'https://img.icons8.com/ios-filled/50/000000/drone.png',
      iconSize: [50, 50]
    });
    var dropIcon = L.icon({
      iconUrl: 'https://img.icons8.com/ios-filled/50/000000/marker.png',
      iconSize: [20, 20]
    });

    var droneMarker = L.marker([0, 0], { icon: droneIcon }).addTo(map);
    var dropMarker = L.marker([0, 0], { icon: dropIcon }).addTo(map);
    var routeLine = L.polyline([], { color: 'green', weight: 5 }).addTo(map);

    // Update Drone Location
    const droneRef = ref(database, "drone_location");
    onValue(droneRef, (snapshot) => {
      const data = snapshot.val();
      console.log("Drone location updated:", data);
      if (data?.latitude && data?.longitude) {
        const dronePosition = [data.latitude, data.longitude];
        droneMarker.setLatLng(dronePosition);
        updateRoute();
      }
    });

    // Update Delivery Location
    const deliveryRef = ref(database, "mission");
    onValue(deliveryRef, (snapshot) => {
      const data = snapshot.val();
      console.log("Delivery location updated:", data);
      if (data?.latitude && data?.longitude) {
        const dropPosition = [data.latitude, data.longitude];
        dropMarker.setLatLng(dropPosition);
        updateRoute();
      }
    });

    // Update route line
    function updateRoute() {
      const dronePos = droneMarker.getLatLng();
      const dropPos = dropMarker.getLatLng();
      if (dronePos && dropPos) {
        routeLine.setLatLngs([dronePos, dropPos]);
      }
    }
  } catch (error) {
    console.error("Error initializing map:", error);
  }
});

console.log("Firebase app.js loaded successfully");
