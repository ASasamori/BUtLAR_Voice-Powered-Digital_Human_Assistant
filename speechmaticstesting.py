import sounddevice as sd
import soundfile as sf
import numpy as np
from speechmatics.client import WebsocketClient
from speechmatics.models import (
    ConnectionSettings,
    AudioSettings,
    TranscriptionConfig,
    ServerMessageType
)
from httpx import HTTPStatusError
import tempfile

# 🔐 Your Speechmatics real-time API key
API_KEY = "API KEY"  # <<< Replace this with your actual key
LANGUAGE = "en"
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5
DTYPE = "int16"

# 🧠 Collect final transcript here
full_transcript = []

print("🎙️ Recording... Speak into your mic for 5 seconds...")

# 🎤 Record audio from Mac mic
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
    filename = tmp_wav.name
    audio = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE)
    sd.wait()
    sf.write(filename, audio, SAMPLE_RATE)
    print(f"✅ Saved recording: {filename}")

# 🌐 Set up Speechmatics client
ws = WebsocketClient(
    ConnectionSettings(
        url="wss://eu2.rt.speechmatics.com/v2",
        auth_token=API_KEY
    )
)

def print_partial(msg):
    print(f"[partial] {msg['metadata']['transcript']}")

def print_full(msg):
    text = msg['metadata']['transcript'].strip()
    print(f"[  FULL ] {text}")
    if text:
        full_transcript.append(text)

ws.add_event_handler(ServerMessageType.AddPartialTranscript, print_partial)
ws.add_event_handler(ServerMessageType.AddTranscript, print_full)

settings = AudioSettings(sample_rate=SAMPLE_RATE)

conf = TranscriptionConfig(
    language=LANGUAGE,
    additional_vocab=[
        {"content": "EC413", "sounds_like": ["E C four one three", "E C four thirteen", "EC for 13", "easy for 13"]},
        {"content": "EC412", "sounds_like": ["E C four one two", "E C four twelve", "EC for 12", "easy for 12"]},
        {"content": "CAS212", "sounds_like": ["C A S two one two", "C A S two twelve", "Cass for 12"]},
        {"content": "EC471", "sounds_like": ["E C four seven one"]}  # Added from your EC 471 context
    ],
    enable_partials=True,
    max_delay=2,
    audio_format="wav"
)

print("📤 Sending to Speechmatics for transcription...")

try:
    with open(filename, "rb") as f:
        ws.run_synchronously(f, conf, settings)
except KeyboardInterrupt:
    print("🛑 Stopped.")
except HTTPStatusError as e:
    if e.response.status_code == 401:
        print("❌ Invalid API key!")
    else:
        raise e

# ✅ Print full transcript at the end
final_result = " ".join(full_transcript).strip()
print("\n📝 Final Transcript:")
print(final_result if final_result else "(no transcription)")
