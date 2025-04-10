import asyncio
import subprocess
import json
import time
import os
import base64
from threading import Thread
from channels.generic.websocket import AsyncWebsocketConsumer

class BUtlARConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.loop = asyncio.get_event_loop()
        
        def run_assistant():
            print("🟢 Starting BUtLAR voice assistant pipeline...")
            cmd = (
                "/home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/miniaudio_stream "
                "| sox -t raw -r 16000 -e signed -b 16 -c 2 - "
                "-t raw -r 16000 -e signed -b 16 -c 1 - "
                "| python3 /home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/main.py"
            )
            process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            
            # Track audio chunks for visualization
            audio_buffer = b''
            chunk_size = 4096  # Matches miniaudio chunk size
            
            for line in iter(process.stdout.readline, ""):
                print(f"FROM ASSISTANT: {line.strip()}")
                text = line.strip()
                
                # Attempt to read audio chunk
                try:
                    chunk = process.stdout.buffer.read(chunk_size)
                    if chunk:
                        # Encode audio chunk to base64 for WebSocket transmission
                        audio_chunk_base64 = base64.b64encode(chunk).decode('utf-8')
                        payload = {
                            "type": "audio_chunk",
                            "data": audio_chunk_base64,
                            "metadata": {
                                "sample_rate": 16000,
                                "format": "s16",
                                "channels": 2
                            }
                        }
                        asyncio.run_coroutine_threadsafe(
                            self.send(text_data=json.dumps(payload)),
                            self.loop
                        )
                except Exception as e:
                    print(f"Audio chunk reading error: {e}")
                
                # Existing payload processing
                if text.startswith("Final transcript:"):
                    payload = {
                        "type": "transcript",
                        "text": text.replace("Final transcript:", "").strip(" '")
                    }
                elif text.startswith("Processing question:"):
                    payload = {
                        "type": "log",
                        "text": text
                    }
                elif text.startswith("Response:"):
                    payload = {
                        "type": "response",
                        "text": text.replace("Response:", "").strip()
                    }
                else:
                    payload = {
                        "type": "log",
                        "text": text
                    }
                
                # Send non-audio payloads
                if payload["type"] != "audio_chunk":
                    asyncio.run_coroutine_threadsafe(
                        self.send(text_data=json.dumps(payload)),
                        self.loop
                    )
                
                time.sleep(0.1)  # Slight delay to prevent overwhelming WebSocket
            
            print("🔴 Assistant process finished.")
            process.stdout.close()
        
        self.assistant_thread = Thread(target=run_assistant, daemon=True)
        self.assistant_thread.start()

    async def disconnect(self, close_code):
        print("🔴 WebSocket disconnected.")

    async def receive(self, text_data):
        # Existing pause/resume logic remains the same
        data = json.loads(text_data)
        msg_type = data.get("type", "")
        flag_dir = "/home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/django_top/butlar/flag"
        flag_file = os.path.join(flag_dir, "responding.flag")
        duration_file = os.path.join(flag_dir, "tts_duration.flag")
        
        if msg_type == "pause":
            os.makedirs(flag_dir, exist_ok=True)
            with open(flag_file, "w") as f:
                f.write("responding")
            if "duration" in data:
                with open(duration_file, "w") as f:
                    f.write(str(data["duration"]))
            print("🛑 Received 'pause' → flag and duration written.")
        
        elif msg_type == "resume":
            with open(flag_file, "w") as f:
                f.write("resume")
            print("▶️ Received 'resume' → flag written.")