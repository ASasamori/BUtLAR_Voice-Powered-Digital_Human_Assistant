from openai import OpenAI
import os

# Initialize OpenAI client
client = OpenAI(api_key="API KEY")

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

Examples:
- Q: What classes does Tali Moreshet teach?
  A: SELECT crse_id, descr FROM classes WHERE instructors LIKE '%Tali Moreshet%';

- Q: When is EC414 discussion?
  A: SELECT days, time, room FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '414' AND component = 'DIS';

- Q: Who teaches EC311?
  A: SELECT DISTINCT instructors FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '311';

- Q: What classes does Professor Pisano teach?
  A: SELECT crse_id, descr FROM classes WHERE instructors LIKE '%Pisano%';

- Q: What room is ENGEC 311 lecture in?
  A: SELECT room FROM classes WHERE subject = 'ENGEC' AND catalog_nbr = '311' AND component = 'LEC';

If a user asks "when is [course]" or "what time is EC[xxx]", assume they are asking about the lecture unless they specifically mention discussion, lab, or another section type. In that case, filter by component accordingly (e.g., 'DIS' for discussion, 'LAB' for lab, etc).

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
