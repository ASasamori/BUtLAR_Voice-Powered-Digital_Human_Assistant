# voice_assistant.py
import os
import sys
import time
from google.cloud import speech
from pathlib import Path
from google.cloud.speech_v1 import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
from test import interpret_vanna_msg

def process_audio_stream():
    script_dir = Path(__file__).resolve().parent

    client = speech.SpeechClient()
    config = RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    streaming_config = StreamingRecognitionConfig(config=config, interim_results=True)

    print("Response: Hi! I'm BUtLAR, here to answer any of your BU-related questions. I'll listen for 30 seconds then respond.")
    print("Say 'Goodbye, BUtLAR!' to stop at any time.")
    sys.stdout.flush()

    def audio_generator():
        while True:
            chunk = sys.stdin.buffer.read(4096)
            if not chunk:
                break
            yield StreamingRecognizeRequest(audio_content=chunk)

    requests = audio_generator()
    responses = client.streaming_recognize(config=streaming_config, requests=requests)

    full_transcript = ""
    start_time = time.time()
    
    try:
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript
            transcript_lower = transcript.strip().lower()

            # Check if user wants to exit
            if "goodbye" in transcript_lower:
                print("Response: I hope I answered your questions. Goodbye!")
                sys.stdout.flush()
                try:
                    sys.stdin.close()
                except:
                    pass
                return

            # Display interim results
            if result.is_final:
                print(f"Transcript: '{transcript}'")
                full_transcript += transcript + " "
                sys.stdout.flush()
            
            # Check if 30 seconds have passed
            current_time = time.time()
            if current_time - start_time >= 30:
                print("\nFinished listening. Processing your question...")
                sys.stdout.flush()
                
                # Process the collected transcript
                if full_transcript:
                    # llm_response = answer_course_question(full_transcript.strip())
                    llm_response = interpret_vanna_msg("Who teaches Computer Organization?")
                    print(f"Response: {llm_response}")
                    print("Say 'Goodbye, BUtLAR!' to exit or ask another question for 30 seconds.")
                else:
                    print("Response: I didn't hear any question. Please try again.")
                
                sys.stdout.flush()
                
                # Reset for the next 30-second session
                full_transcript = ""
                start_time = current_time
                
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