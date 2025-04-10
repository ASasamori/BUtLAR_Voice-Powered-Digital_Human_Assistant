'''Key Changes to Fix the Feedback Loop

Audio Energy Detection: Added an audioop.rms() function to measure the energy level of each audio chunk, helping to distinguish between actual human speech and the assistant's own output.
Time-based Filtering: Implemented logic to ignore audio input immediately after the assistant has spoken, using a last_response_time tracker.
Content-based Filtering: Added detection for phrases like "Response:" or "I'm BUtLAR" to identify when the system is hearing itself.
Improved Flag Timing: Added delays after responses to ensure the system has fully finished speaking before changing flags.
Audio Chunk Filtering: Added logic to skip processing audio chunks that are likely feedback from the system's own output.
Clearer Debugging: Enhanced the debug outputs to help you understand what's being filtered as feedback.

Implementation Notes

You'll need to tune the speech_energy_threshold value based on your specific audio setup. Start with 1500 and adjust higher if it's still picking up its own speech, or lower if it's filtering out valid user input.
I've added a 1.5-second delay after sending responses before switching back to listening mode, which should help prevent the system from hearing the tail end of its own responses.
The code now explicitly looks for signature phrases in the transcribed text that would indicate it's listening to itself."'''

# voice_assistant.py
import os
import sys
import time
import audioop
from google.cloud import speech
from pathlib import Path
from google.cloud.speech_v1 import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
import pandas as pd
import sqlite3
from fullDatabaseRetrieval import answer_course_question_new, answer_course_question
import threading, queue
from pathlib import Path


def process_audio_stream():
    print("DEBUG: Voice Assistant v1.2 - Improved audio feedback handling", file=sys.stderr)
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
    
    # Audio energy threshold to detect actual speech vs background/self noise
    speech_energy_threshold = 1500  # Adjust this value based on testing
    
    # Wait a bit after initial greeting to avoid self-feedback
    time.sleep(1.5)
    
    # Clear the responding flag after greeting
    with open(flag_file, "w") as f:
        f.write("resume")

    # Shared variable to track timeout start time
    timeout_start_time = [time.time()]
    
    # Flag to track if we're currently speaking
    is_speaking = [False]
    
    # Timestamp of last system response
    last_response_time = [time.time()]

    def timeout_check():
        while True:
            elapsed_time = time.time() - timeout_start_time[0]
            # print(f"time is {elapsed_time}")
            if elapsed_time > 45:
                with open(flag_file, "w") as f:
                    f.write("responding")
                print("\nResponse: I didn't detect anyone speaking. I hope I answered your questions. Goodbye!")
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
            
            # Read audio chunk
            chunk = sys.stdin.buffer.read(4096)
            if not chunk:
                break
                
            # Measure audio energy to detect real speech vs system feedback
            energy = audioop.rms(chunk, 2)  # Calculate RMS of audio chunk
            
            # Skip forwarding audio if:
            # 1. We recently sent a response (within 2 seconds)
            # 2. The audio energy is below threshold (likely our own output or background)
            time_since_response = time.time() - last_response_time[0]
            if time_since_response < 2.0 and energy < speech_energy_threshold:
                # This is likely feedback from our own response, skip it
                continue
                
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
            
            # Detect and skip self-feedback - if we get our own response text back
            if "response:" in transcript_lower or "i'm butlar" in transcript_lower:
                print(f"Detected feedback, ignoring: '{transcript}'", file=sys.stderr)
                sys.stderr.flush()
                continue

            # Latency check before processing the transcript
            start_time = time.time()

            # if "goodbye butler" in transcript_lower:
            if "goodbye" in transcript_lower and ("butlar" in transcript_lower or "butler" in transcript_lower):
                with open(flag_file, "w") as f:
                    f.write("responding")
                print("Response: I hope I answered your questions. Goodbye!")
                # Update last response time
                last_response_time[0] = time.time()
                sys.stdout.flush()  # Flush on exit
                try:
                    sys.stdin.close()
                except:
                    pass
                return

            if result.is_final:
                # Skip likely self-responses
                if time.time() - last_response_time[0] < 2.0 and len(transcript) < 50:
                    print(f"Skipping likely feedback: '{transcript}'", file=sys.stderr)
                    sys.stderr.flush()
                    continue
                    
                full_question += transcript + " "
                last_final_time = time.time()
                processed = False
                print(f"Final transcript: '{transcript}'")
                sys.stdout.flush()
                
                if full_question and not processed:
                    # Set responding flag
                    with open(flag_file, "w") as f:
                        f.write("responding")
                    sys.stdout.flush()
                    
                    # Latency check before processing the question
                    question_start_time = time.time()

                    sys.stdout.flush()  # Flush to show processing start

                    # Generate and print response
                    llm_response = answer_course_question(full_question.strip())
                    
                    response_text = f"Response: {llm_response}\n"
                    os.write(1, response_text.encode())
                    
                    # Update last response time
                    last_response_time[0] = time.time()
                    
                    os.write(1, b"Ready for next question...\n")
                    sys.stdout.flush()

                    full_question = ""
                    processed = True                    
                    # RESET the timeout start time after processing
                    timeout_start_time[0] = time.time()
                    
                    # Add a brief delay before changing flag back
                    time.sleep(1.5)  # Wait to ensure response has finished playing
                    
                    # Reset flag to resume listening
                    with open(flag_file, "w") as f:
                        f.write("resume")

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