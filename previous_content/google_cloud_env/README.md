# Google Speech-To-Text 
1) Credentials for authorization established
2) Audio is normalized
3) Audio is broken into chunks for steaming
4) Transcriptions uses V1 Google which is Stable because V2 is still Beta
5) Prints line by line for quicker prints

## Prerequisites
- A Google Cloud account with the Speech-to-Text API enabled.
- A Google service account JSON key file with permissions to access the Speech-to-Text API.
- Python 3.11
- Clone repository
- It's recommended to use a virtual environment to manage dependencies:
python -m venv gcloudenv
source gcloudenv/bin/activate  # On macOS/Linux
- Install dependences: 
pip install pyDub
pip install google-cloud-speech
on mac for pyDub:
brew install ffmpeg

## To Run
python googleTabulate.py audioFile.wav


