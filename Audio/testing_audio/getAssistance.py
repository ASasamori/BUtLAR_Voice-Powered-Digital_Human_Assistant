from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd

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

df = pd.read_csv(script_dir / "database/professors.csv")
lastNames = df["LastName"].tolist()

def lastNamesFunction(userSentence):
    promptLastName = f"""
                You are a helpful assistant tasked with correcting misspelled last names in sentences. 
                I'll provide you with this sentence: "{userSentence}" and this list of existing professor's based on their last names:  
                "{lastNames}". Your job is to:
                1. Identify if this sentence might relate to a last name in the school database. This could include searching for
                an office, office hours, or a class
                Identify any potential last names in the sentence.
                2. If a sentence relates to a last name in the school DB, identify any potential last names in the sentence
                3. Compare the last name to the names in the last names list
                3. If a word closely resembles a last name (e.g., typo or phonetic), replace it with the correct version.
                4. If no corrections are needed, return the sentence unchanged.
                Return only the corrected sentence.
                """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant tasked with last name matching."},
                {"role": "user", "content": promptLastName}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None

def generateSql(user_question):
    prompt = f"""
    You are an expert SQL assistant. Based on user's question, if any relevant info in school.db, generate a SQL query to retrieve the requested information from a SQLite database called 'school.db'. The database has two tables with the following schemas:

    1. Table: professors
       - Columns:
         - LastName (TEXT): Professor's last name (e.g., 'Nawab')
         - FirstName (TEXT): Professor's first name (e.g., 'John')
         - OfficeRoom (TEXT): Office location (e.g., 'Room 101')

    2. Table: offerings
       - Columns:
         - Course (TEXT): Course code (e.g., 'CS101')
         - CourseName (TEXT): Full course name (e.g., 'Introduction to Programming')
         - LastName (TEXT): Professor's last name (e.g., 'Nawab')
         - Time (TEXT): Class time (e.g., 'MWF 10:00-11:00')
         - Location (TEXT): Classroom (e.g., 'Room 305')

    The user's question is: '{user_question}'

    Your task:
    1. Interpret user's question, determine what information they are seeking.
    2. Write SQL query using SQLite syntax to answer the question.
    3. Use JOINs if necessary to combine data from both tables (professors and offerings).
    4. Return only the SQL query as plain text, without any explanations or additional text.

    Example:
    - Question: "Where is Professor Nawab's office?"
    - Query: SELECT OfficeRoom FROM professors WHERE LastName = 'Nawab'
    - Question: "When does Professor Sharifzadeh teach CS101?"
    - Query: SELECT Time FROM offerings WHERE LastName = 'Sharifzadeh' AND Course = 'CS101'
    - Question: "What's Professor Nawab's office and class schedule?"
    - Query: SELECT p.OfficeRoom, o.Time FROM professors p JOIN offerings o ON p.LastName = o.LastName WHERE p.LastName = 'Nawab'

    If the user's question is not found in school.db, return "Sorry, I'm for school search purposes only"
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert SQL assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None

def text_to_speech(text, output_file="text_to_speech_output.mp3"):
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
        return output_path
    except Exception as e:
        print(f"Error in text-to-speech conversion: {e}")
        return None


def respondToUser(userResponse, result):
    """
    Generate a natural language response based on the user's question and SQL result.
    Then convert the response to speech and play it.
    
    Args:
        userResponse (str): The corrected user question.
        result: The result from the SQL query.
    
    Returns:
        str: The LLM-generated response.
    """
    # Check for goodbye message
    if userResponse.lower().strip() in ["goodbye butlar", "goodbye", "bye butlar", "bye"]:
        print("Detected goodbye message, generating goodbye response...")
        generate_goodbye_message("goodbye")
        return "Goodbye!"
    
    promptResponse = f"""
    You are a helpful assistant tasked with responding to the user's questions given the case-specific database. 
    You were asked '{userResponse}' and the answer received from the SQL query is '{result}'. 
    Now return the corresponding answer.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": promptResponse}
            ]
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Convert response to speech and play it
        print("Converting response to speech...")
        audio_file = text_to_speech(response_text)
        print(f"Audio file saved to: {audio_file}")

        return response_text
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None