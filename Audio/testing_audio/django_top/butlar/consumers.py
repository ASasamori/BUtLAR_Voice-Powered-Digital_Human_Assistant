import asyncio
import subprocess
import json
import time
from threading import Thread
from channels.generic.websocket import AsyncWebsocketConsumer

class BUtlARConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.loop = asyncio.get_event_loop()  # Main event loop
        self.pause_flag = False  # Flag to control processing, not audio input
        self.process = None
        
        def run_assistant():
            print("🟢 Starting BUtLAR voice assistant pipeline...")

            # Create a temporary file to pass the pause flag status
            pause_flag_file = "/home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/tmp/butlar_pause_flag"
            
            try:
                # Initialize to "0" (not paused)
                with open(pause_flag_file, "w") as f:
                    f.write("0")
            except Exception as e:
                print(f"Error initializing pause flag file: {e}")

            cmd = (
                "/home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/miniaudio_stream "
                "| sox -t raw -r 16000 -e signed -b 16 -c 2 - "
                "-t raw -r 16000 -e signed -b 16 -c 1 - "
                "| python3 /home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/main.py"
            )

            self.process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )

            for line in iter(self.process.stdout.readline, ""):
                print(f"FROM ASSISTANT: {line.strip()}")
                text = line.strip()

                # Continue normal processing for all messages
                if text.startswith("Final transcript:"):
                    # Only process transcripts when not paused
                    if not self.pause_flag:
                        payload = {
                            "type": "transcript",
                            "text": text.replace("Final transcript:", "").strip(" '")
                        }
                        asyncio.run_coroutine_threadsafe(
                            self.send(text_data=json.dumps(payload)),
                            self.loop
                        )
                elif text.startswith("Processing question:"):
                    payload = {
                        "type": "log",
                        "text": text
                    }
                    asyncio.run_coroutine_threadsafe(
                        self.send(text_data=json.dumps(payload)),
                        self.loop
                    )
                elif text.startswith("Response:"):
                    payload = {
                        "type": "response",
                        "text": text.replace("Response:", "").strip()
                    }
                    asyncio.run_coroutine_threadsafe(
                        self.send(text_data=json.dumps(payload)),
                        self.loop
                    )
                else:
                    payload = {
                        "type": "log",
                        "text": text
                    }
                    asyncio.run_coroutine_threadsafe(
                        self.send(text_data=json.dumps(payload)),
                        self.loop
                    )

            print("🔴 Assistant process finished.")
            if self.process:
                self.process.stdout.close()

        self.assistant_thread = Thread(target=run_assistant, daemon=True)
        self.assistant_thread.start()

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"Received data: {data}")
        if data.get("type") == "pause":
            print("📵 Pausing speech recognition...")
            self.pause_flag = True
            # Write to flag file that assistant should be paused
            print("Writing pause flag to file...")
            try:
                with open("/tmp/butlar_pause_flag", "w") as f:
                    f.write("1")  # 1 means paused
            except Exception as e:
                print(f"Error writing pause flag: {e}")
                
        elif data.get("type") == "resume":
            print("🎙️ Resuming speech recognition...")
            self.pause_flag = False
            # Write to flag file that assistant should resume
            try:
                with open("/tmp/butlar_pause_flag", "w") as f:
                    f.write("0")  # 0 means not paused
            except Exception as e:
                print(f"Error writing resume flag: {e}")

    async def disconnect(self, close_code):
        print("🔴 WebSocket disconnected.")
        if self.process:
            self.process.terminate()