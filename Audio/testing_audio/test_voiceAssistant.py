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

    print("Response: Hi! I'm BUtLAR, here to answer any of your BU-related questions. I'll listen for 5 seconds then respond.")
    print("Say 'Goodbye, BUtLAR!' to stop at any time.")
    sys.stdout.flush()

    def audio_generator():
        start_time = time.time()
        while time.time() - start_time < 5:  # Limit to 5 seconds
            chunk = sys.stdin.buffer.read(4096)
            if not chunk:  # End if no more data to read
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

            # Display interim results
            if result.is_final:
                print(f"Transcript: '{transcript}'")
                full_transcript += transcript + " "
                sys.stdout.flush()

            # Check if 5 seconds have passed (hard stop after this time)
            if time.time() - start_time >= 5:
                print("\nFinished listening. Processing your question...")
                sys.stdout.flush()
                
                # Process the collected transcript
                if full_transcript:
                    # Call the function after 5 seconds
                    lm_response = interpret_vanna_msg("Who teaches Computer Organization?")
                    print(f"Response: {lm_response}")
                else:
                    print("Response: I didn't hear any question. Please try again.")
                
                sys.stdout.flush()

                # Exit the loop to stop the process
                break  # Break out of the loop after processing

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