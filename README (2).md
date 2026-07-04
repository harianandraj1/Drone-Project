# 🚁 Drone Delivery System

A comprehensive autonomous drone delivery system featuring real-time tracking, QR code verification, payload release mechanism, and live video streaming. Built with Firebase, DroneKit, OpenCV, and modern web technologies.

![Drone Delivery System](public/drone%20image.jpg)

## 🎯 Features

### Core Functionality
- **Autonomous Flight Control**: Automated takeoff, navigation, and landing using DroneKit
- **QR Code Verification**: Computer vision-based package verification system
- **Real-time GPS Tracking**: Live drone location updates via Firebase
- **Live Video Streaming**: Real-time camera feed from drone
- **Payload Release**: Servo-controlled package delivery mechanism
- **Mission Planning**: Web-based mission deployment interface

### Technical Highlights
- **Multi-threaded Architecture**: Concurrent GPS updates and video streaming
- **Adaptive Landing System**: Precise landing with QR code guidance
- **Error Handling**: Robust exception handling and mission recovery
- **Cross-platform Compatibility**: Raspberry Pi and laptop integration
- **Real-time Database**: Firebase integration for live updates

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │────│   Firebase DB   │────│   Drone System  │
│   (Frontend)    │    │   (Real-time)   │    │   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐              ┌─────────┐           ┌─────────────┐
    │ Leaflet │              │ Mission │           │ DroneKit    │
    │ Maps    │              │ Control │           │ + Pixhawk   │
    └─────────┘              └─────────┘           └─────────────┘
                                                          │
                                              ┌─────────────────────┐
                                              │ Camera + QR Scanner │
                                              │ Servo Controller    │
                                              └─────────────────────┘
```

## 📁 Project Structure

```
dronedeliverysystem/
├── backend/                    # Drone control and mission logic
│   ├── missioncode.py         # Main mission execution script
│   ├── videostreaming.py      # Flask video streaming server
│   ├── lapqr.py              # QR code scanning and landing
│   ├── dronepython.py        # Core drone control functions
│   ├── firebase_conn_check.py # Firebase connection testing
│   ├── final.py              # Integrated mission controller
│   ├── requirements.txt       # Python dependencies
│   ├── firebase_config.json  # Firebase configuration
│   └── serviceAccountKey.json # Firebase service account
├── public/                    # Web interface
│   ├── index.html            # Main dashboard
│   ├── app.js                # Frontend JavaScript logic
│   ├── styles.css            # UI styling
│   └── drone image.jpg       # Project banner
├── websocket.py              # WebSocket video streaming
├── firebase.json             # Firebase hosting config
├── .firebaserc              # Firebase project settings
└── README.md                # Project documentation
```

## 🚀 Getting Started

### Prerequisites

#### Hardware Requirements
- Pixhawk flight controller
- Raspberry Pi or compatible SBC
- Camera module (Pi Camera or USB webcam)
- Servo motor for payload release
- GPS module
- Telemetry radio (optional)

#### Software Requirements
- Python 3.7+
- Node.js (for Firebase CLI)
- OpenCV
- DroneKit
- Firebase Admin SDK

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd dronedeliverysystem
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Install additional packages for Raspberry Pi**
   ```bash
   pip install picamera2 RPi.GPIO
   ```

4. **Firebase Setup**
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Enable Realtime Database
   - Download service account key and save as `serviceAccountKey.json` in backend/
   - Update Firebase configuration in `public/app.js`

5. **Install Firebase CLI (optional for hosting)**
   ```bash
   npm install -g firebase-tools
   firebase login
   ```

### Configuration

1. **Update connection string in Python files**
   ```python
   # Replace COM4 with your connection string
   vehicle = connect('/dev/ttyUSB0', wait_ready=True, baud=57600)  # Linux
   # or
   vehicle = connect('COM4', wait_ready=True, baud=57600)  # Windows
   ```

2. **Configure GPIO pins (Raspberry Pi)**
   ```python
   SERVO_PIN = 18  # Adjust based on your wiring
   ```

3. **Update Firebase database URL**
   ```python
   'databaseURL': 'https://your-project-default-rtdb.firebaseio.com/'
   ```

## 🎮 Usage

### Starting the System

1. **Launch the web interface**
   ```bash
   firebase serve
   # or for local development
   python -m http.server 8000
   ```

2. **Start the drone mission controller**
   ```bash
   cd backend
   python missioncode.py
   ```

3. **Start video streaming (optional)**
   ```bash
   python videostreaming.py
   # or for WebSocket streaming
   python websocket.py
   ```

### Mission Deployment

1. Open the web interface in your browser
2. Navigate to the "Drone Mission" tab
3. Enter delivery coordinates (latitude/longitude)
4. Input the expected QR code for verification
5. Click "🚀 Deploy Drone"
6. Monitor mission status in real-time

### Live Tracking

1. Switch to "Live Feed & Tracking" tab
2. View real-time video feed from drone camera
3. Monitor drone position on interactive map
4. Track delivery progress and route

## 🔧 API Reference

### Firebase Database Structure

```json
{
  "mission": {
    "latitude": 10.9958668,
    "longitude": 76.7702428,
    "expected_qr": "DELIVERY_123",
    "status": "Deployed",
    "timestamp": 1642345678901
  },
  "drone_location": {
    "latitude": 10.9960000,
    "longitude": 76.7700000,
    "altitude": 10.5,
    "timestamp": 1642345679000
  }
}
```

### Key Functions

#### Mission Control
```python
def main_mission():
    # Main mission execution loop
    # Handles takeoff, navigation, QR verification, landing

def detect_qr_code():
    # QR code detection using OpenCV
    # Returns QR data or None

def release_payload():
    # Servo motor control for package release
```

#### Video Streaming
```python
def generate_frames():
    # Frame generator for Flask streaming
    
def start_camera_stream():
    # Initialize camera and Flask server
```

## 🛠️ Hardware Setup

### Wiring Diagram

```
Pixhawk ──────── Raspberry Pi
   │                 │
   │                 ├── Camera Module
   │                 ├── Servo Motor (GPIO 18)
   │                 └── WiFi/Cellular Module
   │
GPS Module
```

### Servo Connection
- Signal: GPIO 18
- Power: 5V
- Ground: GND

### Camera Setup
- Pi Camera: CSI connector
- USB Camera: USB port
- Configure camera index in code

## 🚨 Safety Features

- **Failsafe Mechanisms**: Automatic RTL on communication loss
- **GPS Validation**: Ensures GPS lock before mission start
- **Battery Monitoring**: Low battery return-to-launch
- **Emergency Stop**: Manual mission abort capability
- **QR Verification**: Prevents wrong deliveries

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check USB/serial connection
   - Verify baud rate (57600)
   - Ensure proper permissions

2. **GPS Not Locked**
   - Move to open area
   - Wait for satellite acquisition
   - Check GPS module connections

3. **Camera Not Working**
   - Verify camera permissions
   - Check camera index (0, 1, etc.)
   - Test with `v4l2-ctl --list-devices`

4. **Firebase Connection Issues**
   - Verify internet connection
   - Check Firebase configuration
   - Validate service account key

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 TODO

- [ ] Add weather condition checking
- [ ] Implement multi-drone support
- [ ] Add delivery scheduling system
- [ ] Integrate with delivery tracking APIs
- [ ] Add mobile app companion
- [ ] Implement machine learning for better landing
- [ ] Add voice commands support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- DroneKit team for the excellent Python API
- Firebase team for real-time database
- OpenCV community for computer vision tools
- ArduPilot project for flight controller firmware

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact: [your-email@example.com]
- Documentation: [project-docs-url]

---

**⚠️ Disclaimer**: This system is for educational and research purposes. Always follow local aviation regulations and safety guidelines when operating drones. The authors are not responsible for any misuse or damage caused by this system.

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2GB | 4GB+ |
| Storage | 16GB | 32GB+ |
| Python | 3.7+ | 3.9+ |
| Camera | 720p | 1080p+ |
| Internet | 1 Mbps | 5 Mbps+ |

---

*Built with ❤️ for autonomous delivery systems*
