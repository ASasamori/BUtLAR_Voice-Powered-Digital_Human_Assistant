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
    """
    Generates SQL queries based on user questions for the eceDay.db schema.
    """
    prompt = f"""
You are a helpful assistant that generates SQL queries for a SQLite database named 'eceDay.db'.

The schema includes:

Table: teams
- team_number (INTEGER)
- team_name (TEXT)
- abstract_summary (TEXT)
- team_members (TEXT)
- team_client (TEXT)
- client_about (TEXT)
- team_location (TEXT)

Table: team_members
- member_id (INTEGER)
- team_member (TEXT)
- team_number (INTEGER)

Instructions:
- Use LOWER(team_name) LIKE LOWER('%...%') for partial team name matching.
- Use team_number = [#] for numeric team lookups.
- If the user asks about team members, JOIN teams and team_members ON team_number.
- Only return the SQL query — no explanations.

Examples:
Q: What is SmoothOperator about?
A: SELECT abstract_summary FROM teams WHERE LOWER(team_name) LIKE LOWER('%SmoothOperator%');

Q: Who is in team 14?
A: SELECT team_member FROM team_members WHERE team_number = 14;

Q: Where is Mini Bots?
A: SELECT team_location FROM teams WHERE LOWER(team_name) LIKE LOWER('%Mini Bots%');

Q: Who is the client for team 3?
A: SELECT team_client FROM teams WHERE team_number = 3;

Q: What is the abstract for BUtLAR?
A: SELECT abstract_summary FROM teams WHERE LOWER(team_name) LIKE LOWER('%BUtLAR%');

Now write the query to answer:
{user_question}

Return only the SQL query.
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
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
