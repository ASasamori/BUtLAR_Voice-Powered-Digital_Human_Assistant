from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path

# PATH SETUP: Get the directory of this script
script_dir = Path(__file__).resolve().parent

# Load API key from .env file
dotenv_path = script_dir / '../../.env'  # Adjust path to match your structure
load_dotenv(dotenv_path=dotenv_path)
open_ai_api_key = os.getenv("open_ai_api_key")
if not open_ai_api_key:
    raise ValueError("OpenAI API key not found in .env file")

# Initialize OpenAI client
client = OpenAI(api_key=open_ai_api_key)

def text_to_speech(text, output_file="goodbye_speech_two.mp3"):
    """
    Convert text to speech using OpenAI's Text-to-Speech API
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",  # You can also use "tts-1-hd" for higher quality
            voice="onyx", 
            input=text,
        )
        
        # Save the audio file
        output_path = script_dir / output_file
        response.stream_to_file(output_path)
        print(f"Audio file saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error in text-to-speech conversion: {e}")
        return None

def generate_goodbye_message(scenario="timeout"):
    """
    Generate and save the appropriate goodbye message based on the scenario.
    
    Args:
        scenario (str): Either "goodbye" for explicit goodbye or "timeout" for session timeout
    """
    goodbye_text_one = "I hope I answered your questions. Goodbye!"
    goodbye_text_two = "I didn't detect anyone speaking. I hope I answered your questions. Goodbye!"
    
    if scenario == "goodbye":
        print("Generating explicit goodbye message...")
        return text_to_speech(goodbye_text_one, "goodbye_speech_one.mp3")
    else:  # timeout
        print("Generating timeout goodbye message...")
        return text_to_speech(goodbye_text_two, "goodbye_speech_two.mp3")

# Only run this if the file is run directly
if __name__ == "__main__":
    # Test both scenarios
    print("Testing goodbye messages...")
    generate_goodbye_message("goodbye")
    generate_goodbye_message("timeout")