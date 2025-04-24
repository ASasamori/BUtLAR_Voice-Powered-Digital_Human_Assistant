# voice_assistant.py
import os
import sys
import time, audioop
from google.cloud import speech
from pathlib import Path
from google.cloud.speech_v1 import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
import pandas as pd
import sqlite3
from fullDatabaseRetrieval import answer_course_question_new, answer_course_question
from test import interpret_vanna_msg
import threading, queue
from pathlib import Path
from sql_database.txtToLLM import text_to_llm
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
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

# PATH SETUP: Get the directory of this script
script_dir = Path(__file__).resolve().parent

# get API key
dotenv_path = script_dir / '../../.env'  # Adjust path to match your structure
load_dotenv(dotenv_path=dotenv_path)
speechmatics_key = os.getenv("SPEECHMATICS_KEY")
if not speechmatics_key:
    raise ValueError("Speechmatics API key not found in .env file")


# 🔐 Your Speechmatics real-time API key
API_KEY = speechmatics_key  
LANGUAGE = "en"
SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5
DTYPE = "int16"

def expand_course_vocab(codes):
    vocab = []
    for code in codes:
        letters = ''.join([c for c in code if c.isalpha()])
        numbers = ''.join([c for c in code if c.isdigit()])
        if not letters or not numbers:
            continue

        # Breakdown numbers
        digits = ' '.join(numbers)
        alt = []
        if len(numbers) == 3:
            alt.append(f"{numbers[0]} {numbers[1]} {numbers[2]}")
            alt.append(f"{numbers[0]} {numbers[1:]}")  # e.g. four twelve
            alt.append(f"{letters.lower()} {numbers[0]} {numbers[1:]}")  # e.g. easy 4 12
        alt.append(f"{letters} {digits}")
        alt.append(f"{letters.lower()} {digits}")
        alt.append(f"{letters.upper()} {digits}")
        alt.append(f"{letters} {numbers}")
        alt.append(f"{letters.lower()} {numbers}")
        alt.append(f"{letters.upper()} {numbers}")
        alt.append(f"{' '.join(letters)} {digits}")  # E C 4 1 3
        alt.append(f"{' '.join(letters)} {numbers}")  # E C 413

        vocab.append({
            "content": code,
            "sounds_like": list(set(alt))  # unique
        })
    return vocab


def process_audio_stream():

    print("DEBUG: Voice Assistant v1.1 - Flag checking enabled", file=sys.stderr)
    sys.stderr.flush()
    
    script_dir = Path(__file__).resolve().parent
    flag_dir = "/home/yobe/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/testing_audio/django_top/butlar/flag"
    flag_file = Path(flag_dir) / "responding.flag"
    
    # Set initial state to responding
    os.makedirs(os.path.dirname(flag_file), exist_ok=True)
    with open(flag_file, "w") as f:
        f.write("responding")
    
    # Initialize speech client
    client = speech.SpeechClient()
    config = RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    streaming_config = StreamingRecognitionConfig(config=config, interim_results=True)
    
    # moved to display right at the start
    print("Response: Hi! I'm BUtLAR, here to answer any of your BU-related questions. I'm listening...")
    sys.stdout.flush() # Ensure startup message displays immediately
    
    # Clear the responding flag after greeting
    with open(flag_file, "w") as f:
        f.write("resume")

    # Shared variable to track timeout start time
    timeout_start_time = [time.time()]

    def timeout_check():
        while True:
            elapsed_time = time.time() - timeout_start_time[0]
            # print(f"time is {elapsed_time}")
            if elapsed_time > 45:
                with open(flag_file, "w") as f:
                    f.write("responding")
                print("\nResponse: I didn't detect anyone speaking. I hope I answered your questions. Goodbye!")
                # play goodbye_speech_two.mp3
                sys.stdout.flush()
                os._exit(0)  # Forcefully exit the entire process
            time.sleep(1)

    # Start timeout monitoring thread
    timeout_thread = threading.Thread(target=timeout_check, daemon=True)
    timeout_thread.start()

    def audio_generator():
        was_paused = False
        duration_file = Path(flag_file.parent) / "tts_duration.flag"
        chunk_rate_per_second = 16000 * 2  # bytes/sec = 16kHz * 2 bytes/sample

        while True:
            flag = "resume"
            if os.path.exists(flag_file):
                with open(flag_file, "r") as f:
                    flag = f.read().strip()

            if flag == "responding":
                if not was_paused:
                    print("🛑 Audio paused (TTS responding)...", file=sys.stderr)
                    sys.stderr.flush()
                    was_paused = True
                time.sleep(0.1)
                # Generate a silent audio chunk (zeros) instead of pausing
                silent_chunk = bytes(4096)  # 4096 bytes of zeros
                yield StreamingRecognizeRequest(audio_content=silent_chunk)
                time.sleep(0.1)  # Control the rate of silent chunks
                continue


            if was_paused:
                # Add a slight delay to wait for audio to finish entering stdin buffer
                time.sleep(1.1)  # <-- small grace period after TTS finishes

                flush_chunks = 20  # safe default
                try:
                    if duration_file.exists():
                        with open(duration_file, "r") as f:
                            duration = float(f.read().strip())
                            # Slightly over-flush (1.2x) to guarantee silence
                            bytes_to_discard = int(duration * 1.4 * chunk_rate_per_second)
                            flush_chunks = max(50, bytes_to_discard // 4096)
                    if flush_chunks is not None:
                        print(f"🔄 Resumed. Flushing {flush_chunks} chunks (~{flush_chunks * 4096 / 32000:.2f}s audio)...", file=sys.stderr)
                        sys.stderr.flush()

                        for _ in range(flush_chunks):
                            _ = sys.stdin.buffer.read(4096)

                        print("Flushed: ✅ Mic buffer flushed. Now capturing fresh audio.", file=sys.stderr)
                        sys.stderr.flush()
                except Exception as e:
                    print(f"⚠️ Error flushing audio: {e}", file=sys.stderr)

                was_paused = False

            chunk = sys.stdin.buffer.read(4096)
            if not chunk:
                break
            yield StreamingRecognizeRequest(audio_content=chunk)

    full_question = ""
    last_final_time = time.time()
    processed = False

    try:
        requests = audio_generator()
        print(f"The type of requests is {type(requests)}")
        responses = client.streaming_recognize(config=streaming_config, requests=requests)

        for response in responses:
             # Allow mid-stream pause detection
            current_flag = "resume"
            if os.path.exists(flag_file):
                with open(flag_file, "r") as f:
                    current_flag = f.read().strip()

            if not response.results: 
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript
            transcript_lower = transcript.strip().lower()

            # Latency check before processing the transcript
            start_time = time.time()

            # if "goodbye butler" in transcript_lower:
            if "goodbye" in transcript_lower and ("butlar" in transcript_lower or "butler" in transcript_lower):
                with open(flag_file, "w") as f:
                    f.write("responding")
                print("Response: I hope I answered your questions. Goodbye!")
                # play goodbye_speech_one.mp3  
                sys.stdout.flush()  # Flush on exit
                try:
                    sys.stdin.close()
                except:
                    pass
                return

            if result.is_final:
                
                full_question += transcript + " "
                last_final_time = time.time()
                processed = False
                print(f"Final transcript: '{transcript}'")
                # print(f"Interim transcript: '{transcript}'", end='\r')
                sys.stdout.flush()
                current_time = time.time()
                if full_question and not processed:
                    # ADDED TO FLAG
                    with open(flag_file, "w") as f:
                        f.write("responding")
                    sys.stdout.flush()  # Ensure the flag is written
                    # print(f"Processing question: '{full_question.strip()}'")

                    # Latency check before processing the question
                    question_start_time = time.time()

                    is_in_LLM = True
                    sys.stdout.flush()  # Flush to show processing start

                    # Generate and print response immediately

                    llm_response = text_to_llm(full_question.strip())

                    os.write(1, f"Response: {llm_response}\n".encode())  # Print immediately with os.write

                    os.write(1, b"Ready for next question...\n")  # Immediate prompt
                    sys.stdout.flush()  # Additional flush for safety

                    full_question = ""
                    processed = True                    
                    # RESET the timeout start time after processing
                    timeout_start_time[0] = time.time()

                    # Latency check after processing the full question
                    end_time = time.time()
                    print(f"Total processing time for transcript: {end_time - start_time} seconds")

    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)
        sys.stdout.flush()
    finally:
        sys.stdout.flush()
        try:
            sys.stdin.close()
        except:
            pass

if __name__ == "__main__":
    process_audio_stream()