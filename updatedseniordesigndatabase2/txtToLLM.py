# txtToLLM.py (SQL-based version)
import pandas as pd
from callLlm import lastNames as call_llm, generateSql, respondToUser
import manualCheck
import sqlite3
import re

# Load user question from transcript or questions.txt
with open("questions.txt", "r") as f:
    user_sentence = f.read().strip()

number_words = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
    'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20
}

def replace_spelled_numbers(text):
    def convert(match):
        word = match.group(0).lower()
        return str(number_words.get(word, word))

    return re.sub(r'\b(' + '|'.join(number_words.keys()) + r')\b', convert, text, flags=re.IGNORECASE)

user_sentence = replace_spelled_numbers(user_sentence)

# Step 1: Manual pre-check for obvious spelling issues
user_sentence = manualCheck.obviousMispellings(user_sentence)

# Step 2: Load instructor last names from CSV
instructor_df = pd.read_csv("team_members_first_last_names.csv")
last_names_list = instructor_df["Last Name"].dropna().unique().tolist()
last_names_list = [name.strip() for name in last_names_list if isinstance(name, str)]
first_names_list = instructor_df["First Name"].dropna().unique().tolist()
first_names_list = [name.strip() for name in last_names_list if isinstance(name, str)]

# Step 3: Ask LLM to correct the professor name (if needed)
prompt_correction = f"""
You are a helpful assistant tasked with correcting misspelled professor last names in a sentence.

You will be given:
- A sentence from a user
- A list of known last names

Your job is to:
1. Detect potential first names first to correct it based on given last name and if last names is not found, match with the last name in the sentence (e.g., "Noah Margolin" → "Noa Margolin" , "Noah Robitshek → "Noah Robitshek")
2. Compare them to the list and correct any likely typos or phonetic matches (e.g., "Salami" → "Salamy").
3. Correct both the first and last name to match known instructors if needed (e.g., 'Sassamori' → 'Sasamori.'). Use the most likely match based on phonetics.
4. Return only the fully corrected version of the sentence. If no change is needed, return it as-is.

Known last names:
{last_names_list}

Known first names: 
{first_names_list}

Sentence:
{user_sentence}

Only return the corrected sentence.
"""
user_sentence = call_llm(prompt_correction)
if user_sentence is None:
    print("LLM failed to correct names. Using original sentence.")
    user_sentence = user_sentence

# Step 4: Generate SQL query using LLM
sql_query = generateSql(user_sentence)
if sql_query is None:
    print("LLM failed to generate SQL. Exiting.")
    exit()

# Clean up any Markdown formatting from the LLM (e.g., ```sql ... ```)
sql_query = sql_query.replace("```sql", "").replace("```", "").strip()


# Step 5: Run the SQL query against the SQLite database
try:
    conn = sqlite3.connect("eceDay.db")
    cursor = conn.cursor()
    cursor.execute(sql_query)
    result = cursor.fetchall()
    conn.close()
except Exception as e:
    print(f"Error running SQL: {e}")
    result = [("Error executing query",)]

# Step 6: Format final natural language response
final_response = respondToUser(user_sentence, result)
# print("\nFinal Answer:")
print(final_response)
