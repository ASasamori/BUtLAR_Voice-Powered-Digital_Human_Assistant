# # txtToLLM.py 
# import pandas as pd
# from callLlm import generateSql, respondToUser
# import sqlite3
# import re

# # Load user question
# with open("questions.txt", "r") as f:
#     user_sentence = f.read().strip()

# # Normalize team name casing and remove hyphens/spaces (e.g., 'Mini-Bots' -> 'MiniBots')
# user_sentence = re.sub(r"\b([A-Z][a-z]*)[-\s]([A-Z][a-z]*)\b", lambda m: m.group(1) + m.group(2), user_sentence, flags=re.IGNORECASE)

# # Replace spelled-out numbers (e.g. "team twelve" → "team 12")
# number_words = {
#     'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
#     'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
#     'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
#     'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
#     'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
#     'twenty': 20
# }

# def replace_spelled_numbers(text):
#     words = text.split()
#     new_words = []

#     for word in words:
#         clean = word.lower().strip("’'s")  
#         if clean in number_words:
#             new_words.append(str(number_words[clean]))
#         else:
#             new_words.append(word)
    
#     return ' '.join(new_words)

# user_sentence = replace_spelled_numbers(user_sentence)

# # Optional: name correction logic
# import manualCheck
# user_sentence = manualCheck.obviousMispellings(user_sentence)

# # Smart name correction (only apply if question has a likely full name)
# def is_potential_name(phrase):
#     words = phrase.strip().split()
#     return len(words) >= 2 and all(w[0].isalpha() and w[0].isupper() for w in words)

# if is_potential_name(user_sentence):
#     df_names = pd.read_csv("team_members_first_last_names.csv")
#     last_names = df_names["Last Name"].dropna().unique().tolist()

#     prompt_correction = f"""
# You are a helpful assistant tasked with correcting misspelled full names in a sentence. Use the following list of known last names:
# {last_names}

# If the sentence contains a misspelled full name (first and last), fix it.
# If no full name is found, leave the sentence unchanged.

# Sentence:
# {user_sentence}

# Return only the corrected sentence.
# """
#     from callLlm import lastNames
#     fixed = lastNames(prompt_correction)
#     if fixed: user_sentence = fixed

# # Step 1: Generate SQL
# sql_query = generateSql(user_sentence)
# if sql_query is None:
#     print("LLM failed to generate SQL. Exiting.")
#     exit()

# sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

# # Step 2: Run the query
# try:
#     conn = sqlite3.connect("eceDay.db")
#     cursor = conn.cursor()
#     cursor.execute(sql_query)
#     result = cursor.fetchall()
#     conn.close()
# except Exception as e:
#     print(f"Error running SQL: {e}")
#     result = [("Error executing query",)]

# # Step 3: Format natural language response
# final_response = respondToUser(user_sentence, result)
# print(final_response)

# txtToLLM.py (ECE Day with updated team name handling)
import pandas as pd
from callLlm import generateSql, respondToUser
import sqlite3
import re

# Load user question
import callLlm  # for name correction
import manualCheck
with open("questions.txt", "r") as f:
    user_sentence = f.read().strip()

# Step 1: Manual pre-check for obvious spelling issues
user_sentence = manualCheck.obviousMispellings(user_sentence)

# Step 2: Load instructor names from CSV
instructor_df = pd.read_csv("team_members_first_last_names.csv")
last_names_list = instructor_df["Last Name"].dropna().unique().tolist()
last_names_list = [name.strip() for name in last_names_list if isinstance(name, str)]
first_names_list = instructor_df["First Name"].dropna().unique().tolist()
first_names_list = [name.strip() for name in first_names_list if isinstance(name, str)]

# Step 3: Ask LLM to correct names in the sentence
prompt_correction = f"""
You are a helpful assistant tasked with correcting misspelled team member names in a sentence.

You will be given:
- A sentence from a user
- A list of known last names
- A list of known first names

Your job is to:
1. Detect potential first names to guide correction based on the matching last name.
2. If a known name is misspelled (e.g., "Salami" → "Salamy", "Noah Margolin" → "Noa Margolin"), correct it.
3. Return the corrected sentence. If no correction is needed, return it as-is.

Known last names:
{last_names_list}

Known first names:
{first_names_list}

Sentence:
{user_sentence}

Only return the corrected sentence.
"""
user_sentence = callLlm.lastNames(prompt_correction) or user_sentence
# Replace spelled-out numbers with digits
number_words = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
    'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
    'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
    'twenty': 20
}

def replace_spelled_numbers(text):
    words = text.split()
    new_words = []
    for word in words:
        clean = word.lower().strip("’'s")
        if clean in number_words:
            new_words.append(str(number_words[clean]))
        else:
            new_words.append(word)
    return ' '.join(new_words)

user_sentence = replace_spelled_numbers(user_sentence)

# Load known team names dynamically from the database
conn = sqlite3.connect("eceDay.db")
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT team_name FROM teams")
known_teams = [row[0] for row in cursor.fetchall() if row[0]]
conn.close()

def safe_merge_team_names(sentence):
    for team in known_teams:
        canonical = team.strip()
        stripped_canonical = re.sub(r'[^a-zA-Z0-9]', '', canonical).lower()

        words = sentence.split()
        for i in range(len(words)):
            for j in range(i+1, len(words)+1):
                chunk = words[i:j]
                normalized_chunk = re.sub(r'[^a-zA-Z0-9]', '', ''.join(chunk)).lower()

                if normalized_chunk == stripped_canonical:
                    words = words[:i] + [canonical] + words[j:]
                    sentence = ' '.join(words)
                    break  # only replace once per team
    return sentence


user_sentence = safe_merge_team_names(user_sentence)


# Generate SQL
sql_query = generateSql(user_sentence)
if sql_query is None:
    print("LLM failed to generate SQL. Exiting.")
    exit()

sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

# Run the SQL
try:
    conn = sqlite3.connect("eceDay.db")
    cursor = conn.cursor()
    cursor.execute(sql_query)
    result = cursor.fetchall()
    conn.close()
except Exception as e:
    print(f"Error running SQL: {e}")
    result = [("Error executing query",)]

# Format response
final_response = respondToUser(user_sentence, result)
print(final_response)
