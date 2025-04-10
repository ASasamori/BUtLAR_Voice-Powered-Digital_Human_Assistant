import asyncio
import subprocess
import json
import time, os
from threading import Thread
from channels.generic.websocket import AsyncWebsocketConsumer

class BUtlARConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.loop = asyncio.get_event_loop()  # Main event loop

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

            for line in iter(process.stdout.readline, ""):
                print(f"FROM ASSISTANT: {line.strip()}")
                text = line.strip()

                if text.startswith("Final transcript:"):
                    payload = {
                        "type": "transcript",
                        "text": text.replace("Final transcript:", "").strip(" '")
                    }
                elif text.startswith("Processing question:"):
                    # Show this right after Final transcript for smoother flow
                    payload = {
                        "type": "log",
                        "text": text  # Keep it as log if you want it in debug
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

                asyncio.run_coroutine_threadsafe(
                    self.send(text_data=json.dumps(payload)),
                    self.loop
                )

            time.sleep(0.5)  # Give time to flush final message to WebSocket
            print("🔴 Assistant process finished.")

            process.stdout.close()

        self.assistant_thread = Thread(target=run_assistant, daemon=True)
        self.assistant_thread.start()

    async def disconnect(self, close_code):
        print("🔴 WebSocket disconnected.")

    async def receive(self, text_data):
        """
        Handle pause/resume signals sent from frontend.
        """
        data = json.loads(text_data)
        msg_type = data.get("type", "")
        flag_dir = "/home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/django_top/butlar/flag"
        # Ensure the directory exists
        os.makedirs(flag_dir, exist_ok=True)
        flag_file = os.path.join(flag_dir, "responding.flag")

        if msg_type == "pause":
            os.makedirs(flag_dir, exist_ok=True)
            with open(flag_file, "w") as f:
                f.write("responding")
            print("🛑 Received 'pause' → flag written.")
        elif msg_type == "resume":
            # resume
            os.makedirs(flag_dir, exist_ok=True)
            with open(flag_file, "w") as f:
                f.write("resume")
            print("▶️ Received 'resume' → flag written.")
