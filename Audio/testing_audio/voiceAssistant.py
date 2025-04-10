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
from Vanna_in_audio.test import interpret_vanna_msg
import threading, queue
from pathlib import Path


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
    print("Response: Hi! I'm BUtLAR\n")
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
        while True:
             # Check flag before processing audio
            if os.path.exists(flag_file):
                with open(flag_file, "r") as f:
                    flag = f.read().strip()
                    if flag == "responding":
                        # Skip reading audio while system is responding
                        time.sleep(0.1)
                        continue
            
            chunk = sys.stdin.buffer.read(4096)
            if not chunk:
                break
            yield StreamingRecognizeRequest(audio_content=chunk)

    requests = audio_generator()
    responses = client.streaming_recognize(config=streaming_config, requests=requests)

    full_question = ""
    last_final_time = time.time()
    processed = False

    try:
        for response in responses:
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

                    # # Generate and print response immediately
                    llm_response = answer_course_question(full_question.strip())

                    os.write(1, f"Response: {llm_response}\n".encode())  # Print immediately with os.write

                    os.write(1, b"Ready for next question...\n")  # Immediate prompt
                    sys.stdout.flush()  # Additional flush for safety

                    # Latency check after processing the question
                    # question_end_time = time.time()
                    # print(f"Question processing time: {question_end_time - question_start_time} seconds")

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