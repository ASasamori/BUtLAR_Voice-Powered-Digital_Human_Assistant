# txtToLLM.py (SQL-based version)
import pandas as pd
from .callLlm import lastNames as call_llm, generateSql, respondToUser
from . import manualCheck
from pathlib import Path
import sqlite3

# wrap this whole thing in a function 
def text_to_llm(prompt):
    # Load user question from transcript or questions.txt
    # with open("questions.txt", "r") as f:
    #     user_sentence = f.read().strip()

    # Step 1: Manual pre-check for obvious spelling issues
    # user_sentence = manualCheck.obviousMispellings(user_sentence)
    user_sentence = manualCheck.obviousMispellings(prompt)

    # Step 2: Load instructor last names from CSV

    # Get the path to the current script directory
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir / "instructors_first_last_names.csv"

    # Load CSV from the correct path
    instructor_df = pd.read_csv(csv_path)
    last_names_list = instructor_df["Last Name"].dropna().unique().tolist()
    last_names_list = [name.strip() for name in last_names_list if isinstance(name, str)]

    # Step 3: Ask LLM to correct the professor name (if needed)
    prompt_correction = f"""
    You are a helpful assistant tasked with correcting misspelled professor last names in a sentence.

    You will be given:
    - A sentence from a user
    - A list of known last names

    Your job is to:
    1. Detect potential last names in the sentence.
    2. Compare them to the list and correct any likely typos or phonetic matches (e.g., "bishop" → "boas").
    3. Correct both the first and last name to match known instructors if needed (e.g., 'Tally Moret' → 'Tali Moreshet'). Use the most likely match based on phonetics.
    4. Return only the fully corrected version of the sentence. If no change is needed, return it as-is.

    Known last names:
    {last_names_list}

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
        # Get the path to the SQLite database
        db_path = script_dir / "school.db"
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
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
    # print("\nFinal Answer:")
    return final_response

# main
if __name__ == "__main__":

    with open("questions.txt", "r") as f:
        user_sentence = f.read().strip()

    text_to_llm(user_sentence)
    print("Script executed successfully.")