import os
import sys
import time
from google.cloud import speech
from pathlib import Path
from google.cloud.speech_v1 import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
from openai import OpenAI
from dotenv import load_dotenv

# Get the directory of the current script
script_dir = Path(__file__).resolve().parent

# Initialize OpenAI client
dotenv_path = script_dir / '../../.env'
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv("open_ai_api_key")

# print(f"The value of the api key is {api_key}")

### This is for streaming the audio and transcribing it locally (NOT THROUGH SSH)
# ./miniaudio_stream | sox -t raw -r 16000 -e signed -b 16 -c 2 - -t raw -r 16000 -e signed -b 16 -c 1 - | python3 transcribe_stream.py


def process_audio_stream():
    client = speech.SpeechClient()
    
    config = RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        # enable_spoken_emojis=True,
        enable_automatic_punctuation=True
    )

    streaming_config = StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )
 
    def audio_generator():
        while True:
            chunk = sys.stdin.buffer.read(4096)
            if not chunk:
                print("End of audio stream.", file=sys.stderr)
                break
            yield StreamingRecognizeRequest(audio_content=chunk)

    requests = audio_generator()
    responses = client.streaming_recognize(
        config=streaming_config,
        requests=requests
    )

    # Variable to accumulate the full question
    full_question = ""
    last_final_time = time.time()  # Track the time of the last final result

    try:
        for response in responses:
            if not response.results:
                print("No results in response.", file=sys.stderr)
                continue

            result = response.results[0]
            if not result.alternatives:
                print("No alternatives in result.", file=sys.stderr)
                continue

            transcript = result.alternatives[0].transcript

            if result.is_final:
                # Append the final transcript to the full question
                full_question += transcript + " "
                last_final_time = time.time()  # Update the time of the last final result
                print(f"Final transcript: {transcript}")
            else:
                print(f"Interim transcript: {transcript}", end='\r')
                
            sys.stdout.flush()

            # Check if 3 seconds have passed since the last final result
            current_time = time.time()
            if full_question and (current_time - last_final_time >= 3):
                # Call the OpenAI LLM with the full accumulated question
                try:
                    print(f"Sending to LLM: {full_question.strip()}")
                    llm_response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": full_question.strip()}
                        ],
                        max_tokens=150
                    )
                    answer = llm_response.choices[0].message.content.strip()
                    print(f"LLM Response: {answer}")
                    # Reset the full question after processing
                    full_question = ""
                except Exception as e:
                    print(f"Error calling OpenAI API: {str(e)}", file=sys.stderr)

    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    process_audio_stream()