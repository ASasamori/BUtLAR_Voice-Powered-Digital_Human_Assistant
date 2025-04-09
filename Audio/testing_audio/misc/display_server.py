#!/usr/bin/env python3
import asyncio
import websockets
import json
import subprocess
import threading
import queue
import signal
import sys
import os
from pathlib import Path

# Communication queues
from_backend = queue.Queue()
to_backend = queue.Queue()

# Flags
running = True
is_listening = False
assistant_process = None

def start_voice_assistant():
    """Start the voice assistant pipeline and capture its output"""
    global assistant_process
    
    try:
        # Command to run your existing pipeline
        cmd = "./miniaudio_stream | sox -t raw -r 16000 -e signed -b 16 -c 2 - -t raw -r 16000 -e signed -b 16 -c 1 - | python3 main.py"
        
        # Start the process
        assistant_process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Thread to read stdout
        def read_stdout():
            while running:
                line = assistant_process.stdout.readline()
                if not line and assistant_process.poll() is not None:
                    break
                    
                line = line.strip()
                if line:
                    print(f"Voice assistant: {line}")
                    
                    # Parse the output and forward to the frontend
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
                            "text": "listening"
                        })
                    # Check for interim transcripts if your system outputs them
                    elif "Interim transcript:" in line:
                        transcript = line.replace("Interim transcript:", "").strip()
                        transcript = transcript.strip("'")
                        from_backend.put({
                            "type": "transcript",
                            "text": transcript,
                            "isFinal": False
                        })
        
        # Thread to read stderr
        def read_stderr():
            while running:
                line = assistant_process.stderr.readline()
                if not line and assistant_process.poll() is not None:
                    break
                    
                line = line.strip()
                if line:
                    print(f"Error: {line}", file=sys.stderr)
        
        # Thread to handle commands sent to the assistant
        def command_handler():
            while running:
                try:
                    cmd = to_backend.get(timeout=0.5)
                    if cmd == "start":
                        # Your assistant might be already running, so this might be a no-op
                        print("Starting voice recognition...")
                    elif cmd == "stop":
                        # Send a signal to stop listening
                        print("Stopping voice recognition...")
                        # You might need to send a specific command to your voice assistant
                        # If your assistant has a way to stop listening via stdin:
                        assistant_process.stdin.write("goodbye butler\n")
                        assistant_process.stdin.flush()
                    elif cmd == "goodbye":
                        # Complete shutdown
                        print("Shutting down voice assistant...")
                        assistant_process.stdin.write("goodbye butler\n")
                        assistant_process.stdin.flush()
                        break
                except queue.Empty:
                    continue
        
        # Start the reader threads
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        cmd_thread = threading.Thread(target=command_handler, daemon=True)
        
        stdout_thread.start()
        stderr_thread.start()
        cmd_thread.start()
        
        return True
        
    except Exception as e:
        print(f"Error starting voice assistant: {e}")
        return False

async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    print("Web client connected")
    
    # Send data from backend to WebSocket
    async def forward_from_backend():
        try:
            while running:
                try:
                    # Non-blocking check for messages from backend
                    message = from_backend.get_nowait()
                    await websocket.send(json.dumps(message))
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed")
                    break
        except Exception as e:
            print(f"Error in forwarding messages: {e}")
    
    # Listen for messages from the frontend
    async def listen_to_frontend():
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"Received from client: {data}")
                    
                    if data.get("type") == "client_ready":
                        print("Client reported ready")
                    elif data.get("type") == "command":
                        command = data.get("command")
                        if command == "start":
                            to_backend.put("start")
                            # If your assistant is not already running, start it
                            if assistant_process is None or assistant_process.poll() is not None:
                                success = start_voice_assistant()
                                if success:
                                    print("Started voice assistant")
                                else:
                                    print("Failed to start voice assistant")
                        elif command == "stop":
                            to_backend.put("stop")
                        elif command == "goodbye":
                            to_backend.put("goodbye")
                            if assistant_process:
                                assistant_process.terminate()
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
    
    # Run both directions concurrently
    await asyncio.gather(
        forward_from_backend(),
        listen_to_frontend()
    )

async def main():
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        global running
        print("Shutting down...")
        running = False
        if assistant_process:
            assistant_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start WebSocket server
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        # Run forever until interrupted
        while running:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())