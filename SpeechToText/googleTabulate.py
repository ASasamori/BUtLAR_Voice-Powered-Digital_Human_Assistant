import os
from google.cloud import speech
from pydub import AudioSegment
from pydub.effects import normalize
import argparse
import time

# Set up credentials
CREDENTIALS_PATH = '/Users/noamargolin/gcloudenv/sanguine-orb-441020-p6-a442ce3d1ed1.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

def normalize_audio(audio_path: str) -> str:
    """Normalize audio file."""
    audio = AudioSegment.from_file(audio_path)
    audio = normalize(audio).set_sample_width(2)
    normalized_path = f"normalized_{os.path.basename(audio_path)}"
    audio.export(normalized_path, format="wav")
    return normalized_path

def audio_chunk_generator(audio_path: str, chunk_size_ms: int = 1000):
    """Generate audio chunks."""
    audio = AudioSegment.from_file(audio_path)
    for i in range(0, len(audio), chunk_size_ms):
        yield audio[i:i + chunk_size_ms].raw_data

def transcribe_streaming_v1(stream_file: str):
    """Stream transcription using Google Speech-to-Text API v1."""
    client = speech.SpeechClient()

    # Normalize audio file
    normalized_file = normalize_audio(stream_file)

    # Recognition configuration
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config)

    # Stream requests
    def requests():
        for chunk in audio_chunk_generator(normalized_file):
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    # Process stream and print transcripts
    responses = client.streaming_recognize(config=streaming_config, requests=requests())
    #fullString to print a sentence all together
    fullString = ''
    print('Transcript')
    for response in responses:
        for result in response.results:
            # FOR LINE BY LINE
            #print(result.alternatives[0].transcript.strip())
            fullString += result.alternatives[0].transcript
    #TO PRINT THE WHOLE SENTENCE TOGETHER:
    print(f"Transcript: {fullString.strip()}")
    os.remove(normalized_file)  # Clean up

    return fullString.strip()

    

# Command-line argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    # Run streaming transcription with the provided file path
    start_test_time = time.time()
    transcript = transcribe_streaming_v1(args.file)
    end_test_time = time.time()
    with open('transcript.txt', 'w') as file:
        file.write(transcript)
    print(f"Total ASR Test Time: {round(start_test_time, end_test_time, 2)}s")
