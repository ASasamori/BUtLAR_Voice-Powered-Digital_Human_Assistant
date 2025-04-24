import manualCheck
import pandas as pd
import callLlm
import sqlite3


# import transcript
with open("../SpeechToText/transcript.txt", "r") as file:
    user_sentence = file.read()

#manual check
user_sentence = manualCheck.obviousMispellings(user_sentence)
print(user_sentence)

df = pd.read_csv("../database/workingWDBs/professors.csv")
lastNames = df["LastName"].tolist()
print(lastNames)

#feed to LLM now

# Construct prompt with dynamic last names
promptLastName = f"""
You are a helpful assistant tasked with correcting misspelled last names in sentences. I’ll provide you with a sentence and a database of correct last names from a CSV file with columns 'Last', 'First', and 'Room'. Your job is to:

1. Identify any potential last names in the sentence.
2. Compare them to the list of correct last names from the 'Last' column of the database.
3. If a word in the sentence closely resembles a last name from the database (e.g., a misspelling), replace it with the correct version. Use your judgment to determine similarity (e.g., small typos or phonetic likeness).
4. If no last names are present or no corrections are needed, return the sentence unchanged.

The database will be provided as a list of last names extracted from the 'Last' column. Do not assume any hardcoded list; use only the names I give you. Here’s the list from the CSV:

{lastNames}

Now, process this sentence: '{user_sentence}'  
Return only the corrected sentence as your output.
"""

# Assume user_sentence is provided, e.g., "where is professor nawads office?"
# Call LLM with prompt (pseudo-code, depends on your LLM API)
userResponse = callLlm.lastNames(promptLastName)
if userResponse is None:
    userResponse = user_sentence  # Fallback to original sentence if LLM fails
print(userResponse)
# now last names are good. so just need to connect to DB

# Generate SQL query based on corrected sentence
sql_query = callLlm.generateSql(userResponse)
if sql_query is None:
    sql_query = "SELECT 'Error: Could not generate SQL query'"  # Fallback
print("Generated SQL query:", sql_query)

# Execute the SQL query
try:
    # Connect to school.db
    conn = sqlite3.connect("../database/workingWDBs/school.db")
    cursor = conn.cursor()

    # Execute the generated query
    cursor.execute(sql_query)
    result = cursor.fetchall()
    print("Query result:", result)
    
    
    # Close connectionx
    conn.close()
except sqlite3.Error as e:
    print(f"Error executing SQL query: {e}")

sayOut = callLlm.respondToUser(userResponse, result)
print(sayOut)