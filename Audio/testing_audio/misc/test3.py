import pyaudio

def list_input_devices():
    audio = pyaudio.PyAudio()
    print("Available audio input devices:\n")
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if device_info["maxInputChannels"] > 0:
            print(f"Index {i}: {device_info['name']} (Default: {'Yes' if i == audio.get_default_input_device_info()['index'] else 'No'})")
    audio.terminate()

list_input_devices()