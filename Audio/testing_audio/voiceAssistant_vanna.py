import time
import pyaudio
import re
from google.cloud import speech
from google.cloud.speech_v1 import StreamingRecognizeRequest, StreamingRecognitionConfig, RecognitionConfig
from six.moves import queue
from call_vanna import interpret_vanna_msg

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream:
    def __init__(self, rate, chunk, device_index=None):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self.device_index = device_index

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        if self.device_index is None:
            self.device_index = self._audio_interface.get_default_input_device_info()["index"]

        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield StreamingRecognizeRequest(audio_content=chunk)

def listen_print_loop(responses):
    full_transcript = ""
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        if result.is_final:
            print(f"Final: {transcript}")
            full_transcript += transcript + " "
            return full_transcript.strip()
        else:
            print(f"Interim: {transcript}", end="\r")

    return full_transcript.strip()

def clean_after_punctuation(text):
    punctuation_marks = r"[.!?]"
    match = re.search(punctuation_marks, text)
    if match:
        first_punct_index = match.end()
        cleaned_text = text[:first_punct_index]
        rest_of_text = re.sub(r"[^a-zA-Z\s]", "", text[first_punct_index:])
        return cleaned_text + rest_of_text.strip()
    else:
        return text

def main():
    client = speech.SpeechClient()
    config = RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )
    streaming_config = StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    device_index = None

    print("Listening... (say 'goodbye' to exit)")
    with MicrophoneStream(RATE, CHUNK, device_index=device_index) as stream:
        while True:
            audio_generator = stream.generator()
            responses = client.streaming_recognize(config=streaming_config, requests=audio_generator)
            transcript = listen_print_loop(responses)

            if not transcript:
                continue  # Nothing captured, go again

            cleaned_transcript = clean_after_punctuation(transcript)
            lowered = cleaned_transcript.lower()

            if "goodbye" in lowered or "bye" in lowered or "bye butler" in lowered:
                print("Goodbye detected. Exiting...")
                break

            print(f"\nCalling interpret_vanna_msg with transcript: {cleaned_transcript}")
            llm_response = interpret_vanna_msg(cleaned_transcript)
            print(f"LLM Response: {llm_response}\n")
            print("Ready for next question. Listening...")

if __name__ == "__main__":
    main()