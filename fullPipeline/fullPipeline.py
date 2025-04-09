import os, sys, time, io, torch, whisper
import numpy as np
import soundfile as sf
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import callLlm

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
    """Captures and transcribes live audio using Whisper AI."""
    model_size = "tiny.en"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)

    full_question = ""
    last_final_time = time.time()

    def audio_generator():
        buffer = bytearray()
        while True:
            print("in audio stream function")
            chunk = sys.stdin.buffer.read(4096)  # Read raw PCM audio
            if not chunk:
                print("End of audio stream.", file=sys.stderr)
                break
            buffer.extend(chunk)
            if len(buffer) >= 32000:  # Process every ~1s of 16kHz audio (assuming 16-bit mono)
                yield bytes(buffer[:32000])
                buffer = buffer[32000:]

    for audio_chunk in audio_generator():
        try:
            print("Processing audio chunk...")  # Debug print
            # Convert raw PCM to NumPy array
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

            print(f"Converted {len(audio_np)} samples to float format.")  # Debugging print

            # Save to a temporary file (Whisper requires a file input)
            with io.BytesIO() as temp_wav:
                sf.write(temp_wav, audio_np, 16000, format='WAV')
                temp_wav.seek(0)

                print("Sending to Whisper model...")  # Debug print
                result = model.transcribe(temp_wav)
            
            transcript = result["text"].strip()

            if transcript:
                full_question += transcript + " "
                last_final_time = time.time()
                print(f"Final transcript: {transcript}")
                
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

'''
Audio Stream Capture through Rode -> Calls Miniaudio + Whisper/ASR script (to transcribe)
-> Streams message and text_to_LLM.py (has access to edge case functions)
'''
