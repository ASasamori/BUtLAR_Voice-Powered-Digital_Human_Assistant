import os
import sys
import time
from google.cloud import speech
from pathlib import Path
from google.cloud.speech_v1 import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import sqlite3

# Get the directory of the current script
script_dir = Path(__file__).resolve().parent

# Initialize OpenAI client
dotenv_path = script_dir / '../../.env'
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv("open_ai_api_key")
openai_client = OpenAI(api_key=api_key)


# print(f"The value of the api key is {api_key}")

### This is for streaming the audio and transcribing it locally (NOT THROUGH SSH)
# ./miniaudio_stream | sox -t raw -r 16000 -e signed -b 16 -c 2 - -t raw -r 16000 -e signed -b 16 -c 1 - | python3 transcribe_stream.py


def lastNamesFunction(prompt):
    """
    Call OpenAI LLM to process a prompt and return the corrected sentence.
    
    Args:
        prompt (str): The prompt containing instructions and the sentence to correct.
    
    Returns:
        str: The corrected sentence from the LLM.
    """
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use the same model as your boilerplate
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None  # Return None or handle error as needed
    
def generateSql(user_question, prompt):
    """
    Call OpenAI LLM to generate a SQL query based on a user question and the school.db schema.
    
    Args:
        user_question (str): The user’s question with corrected last names.
    
    Returns:
        str: The generated SQL query.
    """

    try:
        completion = openai_client.chat.completions.create(
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



def respondToUser(userResponse, result):
    promptResponse = f"""
    You are a helpful assistant tasked with responding to the users questions given the case specific database. 
    You were asked
    {userResponse} and the answer received from the SQL query is '{result}'  
    Now return the corresponding answer
    """

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use the same model as your boilerplate
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": promptResponse}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None  # Return None or handle error as needed
    



def process_audio_stream():
    # creates google asr client
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
    
    # infinite running unless silence
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
            print(f"response: {response}*****************************************")
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
                if (transcript.strip().lower() == "goodbye butler."):
                    print("Thanks for talking to me. I hope I answered your questions. Goodbye!")
                    exit()
                
            sys.stdout.flush()

            # openai_client = OpenAI(api_key=api_key)

            df = pd.read_csv("database/professors.csv")
            lastNames = df["LastName"].tolist()

            # Construct prompt with dynamic last names
            promptLastName = f"""
            You are a helpful assistant tasked with correcting misspelled last names in sentences. I’ll provide you with a sentence and a database of correct last names from a CSV file with columns 'Last', 'First', and 'Room'. Your job is to:

            1. Identify any potential last names in the sentence.
            2. Compare them to the list of correct last names from the 'Last' column of the database.
            3. If a word in the sentence closely resembles a last name from the database (e.g., a misspelling), replace it with the correct version. Use your judgment to determine similarity (e.g., small typos or phonetic likeness).
            4. If no last names are present or no corrections are needed, return the sentence unchanged.

            The database will be provided as a list of last names extracted from the 'Last' column. Do not assume any hardcoded list; use only the names I give you. Here’s the list from the CSV:

            {lastNames}

            Now, process this sentence: '{full_question}'  
            Return only the corrected sentence as your output.
            """

            # Define the database schema in the prompt
            sqlPrompt = f"""
            You are an expert SQL assistant. Based on the user’s question, generate a SQL query to retrieve the requested information from a SQLite database called 'school.db'. The database has two tables with the following schemas:

            1. Table: professors
            - Columns:
                - LastName (TEXT): Professor’s last name (e.g., 'Nawab')
                - FirstName (TEXT): Professor’s first name (e.g., 'John')
                - OfficeRoom (TEXT): Office location (e.g., 'Room 101')

            2. Table: offerings
            - Columns:
                - Course (TEXT): Course code (e.g., 'CS101')
                - CourseName (TEXT): Full course name (e.g., 'Introduction to Programming')
                - LastName (TEXT): Professor’s last name (e.g., 'Nawab')
                - Time (TEXT): Class time (e.g., 'MWF 10:00-11:00')
                - Location (TEXT): Classroom (e.g., 'Room 305')

            The user’s question is: '{full_question}'

            Your task:
            1. Interpret the user’s question to determine what information they are seeking.
            2. Write a SQL query using SQLite syntax to answer the question.
            3. Use JOINs if necessary to combine data from both tables (professors and offerings).
            4. Return only the SQL query as plain text, without any explanations or additional text.

            Example:
            - Question: "Where is Professor Nawab’s office?"
            - Query: SELECT OfficeRoom FROM professors WHERE LastName = 'Nawab'
            - Question: "When does Professor Sharifzadeh teach CS101?"
            - Query: SELECT Time FROM offerings WHERE LastName = 'Sharifzadeh' AND Course = 'CS101'
            - Question: "What’s Professor Nawab’s office and class schedule?"
            - Query: SELECT p.OfficeRoom, o.Time FROM professors p JOIN offerings o ON p.LastName = o.LastName WHERE p.LastName = 'Nawab'
            """


            # Check if 3 seconds have passed since the last final result
            current_time = time.time()
            if full_question and (current_time - last_final_time >= 3):

                userResponse = lastNamesFunction(promptLastName)
                if userResponse is None:
                    userResponse = full_question  # Fallback to original sentence if LLM fails
                print(userResponse)


                # Generate SQL query based on corrected sentence
                sql_query = generateSql(userResponse, sqlPrompt)
                if sql_query is None:
                    sql_query = "SELECT 'Error: Could not generate SQL query'"  # Fallback
                print("Generated SQL query:", sql_query)

                # Execute the SQL query
                try:
                    # Connect to school.db
                    conn = sqlite3.connect("database/school.db")
                    cursor = conn.cursor()

                    # Execute the generated query
                    cursor.execute(sql_query)
                    result = cursor.fetchall()
                    print("Query result:", result)
                    
                    # Close connectionx
                    conn.close()
                except sqlite3.Error as e:
                    print(f"Error executing SQL query: {e}")

                # Call the OpenAI LLM with the full accumulated question
                llm_response = respondToUser(userResponse, result)

    except Exception as e:
        print(f"Error occurred: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    process_audio_stream()

'''
Audio Stream Capture through Rode -> Calls Miniaudio + Whisper/ASR script (to transcribe)
-> Streams message and text_to_LLM.py (has access to edge case functions)
'''
