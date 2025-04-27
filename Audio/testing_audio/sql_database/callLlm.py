from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import sys
import os

# PATH SETUP: Get the directory of this script
script_dir = Path(__file__).resolve().parent

# Load API key from .env file
dotenv_path = script_dir / '../../../.env'  # Adjust path to match your structure
# print (f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)
open_ai_api_key = os.getenv("open_ai_api_key")
if not open_ai_api_key:
    raise ValueError("OpenAI API key not found in .env file")

# Initialize OpenAI client
client = OpenAI(api_key=open_ai_api_key)


def lastNames(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None

def generateSql(user_question):
    user_question = user_question.upper()
    prompt = f"""
You are an expert SQL assistant. Based on the user’s question, generate a SQL query to retrieve the requested information from a SQLite database called 'school.db'.

The database contains one table:

Table: classes
- subject (TEXT): e.g. 'ENGEC'
- catalog_nbr (TEXT): e.g. '311'
- crse_id (TEXT): internal ID, not useful for querying
- descr (TEXT): Full course name (e.g., 'Introduction to Logic Design')
- component (TEXT): Type (e.g., 'LEC', 'DIS')
- class_section (TEXT): e.g., 'A1'
- start_dt (TEXT): e.g., '2025-01-16'
- end_dt (TEXT): e.g., '2025-05-10'
- class_nbr (TEXT): e.g., '12345'
- instructors (TEXT): e.g., 'Tali Moreshet'
- campus_descr (TEXT): e.g., 'CRC'
- days (TEXT): e.g., 'MoWeFr'
- time (TEXT): e.g., '2:30 PM - 4:15 PM'
- room (TEXT): e.g., 'PHO 210'

Use subject + catalog_nbr for identifying courses (e.g., subject = 'ENGEC' AND catalog_nbr = '311'). Do NOT rely on crse_id for queries.

Course codes should be interpreted case-insensitively (e.g., 'ec330' and 'EC330' should be treated the same).

Examples:
- Q: When is EC330?
  A: SELECT days, time, room FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '330' AND component = 'LEC';

- Q: What classes does Tali Moreshet teach?
  A: SELECT crse_id, descr FROM classes WHERE instructors LIKE '%Tali Moreshet%';

- Q: When is EC414 discussion?
  A: SELECT days, time, room FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '414' AND component = 'DIS';

- Q: Who teaches EC311?
  A: SELECT DISTINCT instructors FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '311';

- Q: What classes does Professor Pisano teach?
  A: SELECT crse_id, descr FROM classes WHERE instructors LIKE '%Pisano%';

- Q: Who teaches Physics of Semiconductor Devices?
  A: SELECT DISTINCT instructors FROM classes WHERE descr LIKE '%Physics of Semiconductor Devices%';

- Q: What room is ENGEC 311 lecture in?
  A: SELECT room FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '311' AND component = 'LEC';

If a user asks "when is [course]" or "what time is EC[xxx]", assume they are asking about the lecture unless they specifically mention discussion, lab, or another section type. In that case, filter by component accordingly (e.g., 'DIS' for discussion, 'LAB' for lab, etc).

If the user refers to a course by its full name (from the 'descr' column), match it using:
WHERE descr LIKE '%<course name>%'
For example, for "Who teaches Physics of Semiconductor Devices?" use:
SELECT DISTINCT instructors FROM classes WHERE descr LIKE '%Physics of Semiconductor Devices%';

User Question: {user_question}
Return only the SQL query.
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
You are a helpful assistant tasked with responding to a user's question based on a SQL query result.

The user asked:
{userResponse}

The raw SQL result was:
{result}

Now return a natural-sounding answer in a full sentence that directly responds to the user's question.
"""
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": promptResponse}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None