import os
import whisper
import torch
from pydub import AudioSegment
from pydub.effects import normalize
import argparse
import time

def normalize_audio(audio_path: str) -> str:
    """Normalize and convert audio file to 16kHz WAV."""
    audio = AudioSegment.from_file(audio_path)
    audio = normalize(audio).set_sample_width(2).set_frame_rate(16000).set_channels(1)
    
    normalized_path = f"normalized_{os.path.basename(audio_path)}"
    audio.export(normalized_path, format="wav")
    return normalized_path

def transcribe_whisper(audio_path: str, model_size="base"):
    """Transcribe an audio file using OpenAI Whisper."""
    # Load Whisper model (choose 'tiny', 'base', 'small', 'medium', or 'large')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)
    
    # Normalize the audio file
    normalized_file = normalize_audio(audio_path)
    
    # Transcribe the file
    result = model.transcribe(normalized_file)
    transcript = result["text"]

    print(f"Transcript: {transcript.strip()}")
    os.remove(normalized_file)  # Clean up

    return transcript.strip()
    
# Command-line argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to the audio file")
    parser.add_argument("--model_size", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    args = parser.parse_args()

    # Run transcription
    start_time = time.time()
    transcript = transcribe_whisper(args.file, model_size=args.model_size)
    end_time = time.time()

    # Save transcript to file
    with open('transcript.txt', 'w') as file:
        file.write(transcript)
    
    print(f"Total ASR Test Time: {round(end_time - start_time, 2)}s")