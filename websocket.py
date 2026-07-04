import cv2
import asyncio
import websockets
import json
import base64
import threading
import time

class WebRTCVideoStreamer:
    def __init__(self, camera_index=0):
        self.camera = cv2.VideoCapture(camera_index)
        self.clients = set()
        self.frame = None
        self.frame_lock = threading.Lock()

    def capture_frames(self):
        while True:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            with self.frame_lock:
                self.frame = frame

            time.sleep(0.03)  # ~30 FPS

    async def handle_client(self, websocket, path):
        self.clients.add(websocket)
        try:
            while True:
                with self.frame_lock:
                    if self.frame is not None:
                        # Compress and encode frame
                        _, buffer = cv2.imencode('.jpg', self.frame)
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send frame
                        await websocket.send(json.dumps({
                            'type': 'frame',
                            'data': frame_base64
                        }))
                
                await asyncio.sleep(0.1)  # Controlled frame rate
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            self.clients.remove(websocket)

    def start_streaming(self):
        # Start frame capture in a separate thread
        capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        capture_thread.start()

        # Start WebSocket server
        start_server = websockets.serve(self.handle_client, "0.0.0.0", 8765)
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    streamer = WebRTCVideoStreamer()
    streamer.start_streaming()