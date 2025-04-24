# callLlm.py
from openai import OpenAI
import os
from dotenv import load_dotenv
# Load API key from file (assuming it's in the same directory as callLlm.py)

load_dotenv(dotenv_path="/Users/noamargolin/Desktop/BUtLAR_Voice-Powered-Digital_Human_Assistant/.env")
open_ai_api_key = os.getenv("open_ai_key")
print(f"The value is {open_ai_api_key}")
# Initialize OpenAI client
client = OpenAI(api_key=open_ai_api_key)

def lastNames(prompt):
    """
    Call OpenAI LLM to process a prompt and return the corrected sentence.
    
    Args:
        prompt (str): The prompt containing instructions and the sentence to correct.
    
    Returns:
        str: The corrected sentence from the LLM.
    """
    try:
        completion = client.chat.completions.create(
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
    
def generateSql(user_question):
    """
    Call OpenAI LLM to generate a SQL query based on a user question and the school.db schema.
    
    Args:
        user_question (str): The user’s question with corrected last names.
    
    Returns:
        str: The generated SQL query.
    """
    # Define the database schema in the prompt
    prompt = f"""
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

    The user’s question is: '{user_question}'

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

def respondToUser(userResponse, result):
    promptResponse = f"""
    You are a helpful assistant tasked with responding to the users questions given the case specific database. 
    You were asked
    {userResponse} and the answer received from the SQL query is '{result}'  
    Now return the corresponding answer
    """

    try:
        completion = client.chat.completions.create(
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
    