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
    user_question = user_question.upper()
    prompt = f"""
You are an expert SQL assistant. Based on the user’s question, generate a SQL query to retrieve the requested information from a SQLite database called 'eceDay.db'.

The database contains two tables:

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

You should be able to answer questions like:
- "Where is (NAME)'s table?"
- "What is (TEAM)'s group about?"
- "Where is (TEAM)?"
- "What is (NAME)'s project about?"
- "Who are the members in (TEAM)?"
- "Who is the client for (TEAM)?"

Examples:
- Q: Where is John Smith's table?
  A: SELECT team_location FROM teams WHERE team_members LIKE '%John Smith%';

- Q: What is Team Alpha's group about?
  A: SELECT abstract_summary FROM teams WHERE team_name LIKE '%Team Alpha%';

- Q: Where is Team Beta?
  A: SELECT team_location FROM teams WHERE team_name LIKE '%Team BUtLAR%';

- Q: What is John Smith's project about?
  A: SELECT abstract_summary FROM teams WHERE team_members LIKE '%John Smith%';

- Q: Who are the members in Team Gamma?
  A: SELECT team_members FROM teams WHERE team_name LIKE '%Team Gamma%';

- Q: Who is the client for Team Delta?
  A: SELECT team_client FROM teams WHERE team_name LIKE '%Team Delta%';

Important Instructions:
- Always use LIKE '%...'% for flexible matching.
- If a person’s name is given, match against team_members.
- If a team name is given, match against team_name.
- If a team number is given, match against team_number
- If a team location is asked, match against team_location
- After answering any question, add: "If you want more information, go to **[team_location]**."

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
