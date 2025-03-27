# voice_assistant.py
import os
import sys
import time
from google.cloud import speech
from pathlib import Path
from google.cloud.speech_v1 import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
import pandas as pd
import sqlite3
from getAssistance import lastNamesFunction, generateSql, respondToUser
import threading

# flag for when the sentence is being processed. have audio sleep while that happens
is_in_LLM = False

def process_audio_stream():

    global is_in_LLM

    script_dir = Path(__file__).resolve().parent

    client = speech.SpeechClient()
    config = RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    streaming_config = StreamingRecognitionConfig(config=config, interim_results=True)

    # moved to display right at the start
    print("Hi! I'm BUtLAR, here to answer any of your BU-related questions. I'm listening...\nSay 'Goodbye, BUtLAR!' to stop.")
    sys.stdout.flush()  # Ensure startup message displays immediately

    # Shared variable to track timeout start time
    timeout_start_time = [time.time()]

    def timeout_check():
        while True:
            elapsed_time = time.time() - timeout_start_time[0]
            # print(f"time is {elapsed_time}")
            if elapsed_time > 60:
                print("\nI didn't detect anyone speaking. I hope I answered your questions. Goodbye!")
                # play goodbye_speech_two.mp3
                sys.stdout.flush()
                os._exit(0)  # Forcefully exit the entire process
            time.sleep(1)

    # Start timeout monitoring thread
    timeout_thread = threading.Thread(target=timeout_check, daemon=True)
    timeout_thread.start()

    def audio_generator():
        while True:
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
            if "goodbye" in transcript_lower:
                print("I hope I answered your questions. Goodbye!")
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
                    print(f"Processing question: '{full_question.strip()}'")

                    # Latency check before processing the question
                    question_start_time = time.time()

                    is_in_LLM = True
                    sys.stdout.flush()  # Flush to show processing start
                    userResponse = lastNamesFunction(full_question.strip())
                    sql_query = generateSql(userResponse) if not None else "SELECT 'Error...'"

                    try:
                        conn = sqlite3.connect(script_dir / "database/school.db")
                        cursor = conn.cursor()
                        cursor.execute(sql_query)
                        result = cursor.fetchall()
                        conn.close()
                    except sqlite3.Error as e:
                        # print(f"Error executing SQL query: {e}")
                        result = "Error"
                    # Generate and print response immediately
                    llm_response = respondToUser(userResponse, result)
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