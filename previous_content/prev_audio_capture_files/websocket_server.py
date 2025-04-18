#!/usr/bin/env python3
import asyncio
import websockets
import json
import subprocess
import threading
import queue
import sys
import os
from pathlib import Path

# Communication queues
to_backend = queue.Queue()
from_backend = queue.Queue()

# Path to the voice assistant script
script_dir = Path(__file__).resolve().parent
voice_assistant_path = script_dir / "voice_assistant.py"

def backend_thread_function():
    """Thread function to run the voice assistant backend"""
    try:
        process = subprocess.Popen(
            [sys.executable, str(voice_assistant_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            universal_newlines=True,
        )
        
        # Thread for reading from the backend
        def reader_thread():
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                line = line.strip()
                print(f"Backend output: {line}")
                
                if line.startswith("Final transcript:"):
                    transcript = line.replace("Final transcript:", "").strip()
                    transcript = transcript.strip("'")
                    from_backend.put({
                        "type": "transcript",
                        "text": transcript,
                        "isFinal": True
                    })
                elif line.startswith("Response:"):
                    response = line.replace("Response:", "").strip()
                    from_backend.put({
                        "type": "response",
                        "text": response
                    })
                elif "Ready for next question" in line:
                    from_backend.put({
                        "type": "status",
                        "text": "ready"
                    })
        
        # Start reader thread
        threading.Thread(target=reader_thread, daemon=True).start()
        
        # Send data to the backend
        while True:
            try:
                data = to_backend.get(timeout=0.1)
                if data is None:  # Exit signal
                    break
                
                if isinstance(data, dict) and data.get("type") == "command":
                    if data.get("command") == "goodbye":
                        process.stdin.write("goodbye butler\n")
                        process.stdin.flush()
                        break
                elif isinstance(data, dict) and data.get("type") == "audio":
                    # Convert Int16Array back to binary
                    audio_data = bytes(data.get("data", []))
                    process.stdin.buffer.write(audio_data)
                    process.stdin.buffer.flush()
            except queue.Empty:
                continue
        
        process.terminate()
        
    except Exception as e:
        print(f"Error in backend thread: {e}")

async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    print("Client connected")
    
    # Start backend thread if not already running
    backend_thread = threading.Thread(target=backend_thread_function, daemon=True)
    backend_thread.start()
    
    # Send data from WebSocket to backend thread
    async def forward_to_backend():
        try:
            async for message in websocket:
                data = json.loads(message)
                to_backend.put(data)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
        finally:
            # Signal backend thread to exit
            to_backend.put(None)
    
    # Send data from backend thread to WebSocket
    async def forward_from_backend():
        try:
            while True:
                try:
                    # Non-blocking check for messages from backend
                    message = from_backend.get_nowait()
                    await websocket.send(json.dumps(message))
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
    
    # Run both communication directions concurrently
    await asyncio.gather(
        forward_to_backend(),
        forward_from_backend()
    )

async def main():
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())