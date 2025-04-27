import time
import pyaudio
import wave
from faster_whisper import WhisperModel
from test import interpret_vanna_msg

RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 10
OUTPUT_FILENAME = "temp_audio.wav"

def record_audio(filename):
    print("Recording...")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save as WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def transcribe_with_whisper(filename):
    model = WhisperModel("base", compute_type="int8")  # "medium" or "large" for better accuracy
    segments, info = model.transcribe(filename)

    final_text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        final_text += segment.text + " "
    
    return final_text.strip()

def main():
    record_audio(OUTPUT_FILENAME)
    transcript = transcribe_with_whisper(OUTPUT_FILENAME)

    print(f"\nFinal Transcript: {transcript}")
    print("\nCalling interpret_vanna_msg...")
    llm_response = interpret_vanna_msg(transcript)
    print(f"LLM Response: {llm_response}")

if __name__ == "__main__":
    main()