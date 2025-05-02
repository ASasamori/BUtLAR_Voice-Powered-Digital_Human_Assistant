import pandas as pd
import sqlite3
import re
from pathlib import Path
from .callLlm import generateSql, respondToUser, lastNames
from . import manualCheck

def text_to_llm(prompt):
    """
    Process a natural language query about ECE Day by:
    1. Correcting spelling issues
    2. Correcting team member names
    3. Converting the query to SQL
    4. Running the SQL against the database
    5. Returning a natural language response
    
    Args:
        prompt (str): User's natural language query
        
    Returns:
        str: Natural language response to the user's query
    """
    # Step 1: Manual pre-check for obvious spelling issues
    user_sentence = manualCheck.obviousMispellings(prompt)
    
    # Step 2: Load team member names from CSV
    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir / "team_members_first_last_names.csv"
    
    instructor_df = pd.read_csv(csv_path)
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
    corrected_sentence = lastNames(prompt_correction)
    if corrected_sentence:
        user_sentence = corrected_sentence
    
    # Replace spelled-out numbers with digits
    user_sentence = replace_spelled_numbers(user_sentence)
    
    # Load known team names dynamically from the database
    db_path = script_dir / "eceDay.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team_name FROM teams")
    known_teams = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    # Merge team names if found in the sentence
    user_sentence = safe_merge_team_names(user_sentence, known_teams)
    
    # Generate SQL
    sql_query = generateSql(user_sentence)
    if sql_query is None:
        return "Failed to generate SQL query for your question."
    
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    
    # Run the SQL
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        conn.close()
    except Exception as e:
        error_message = f"Error running SQL: {e}"
        print(error_message)
        return f"Sorry, there was no matching data for your query. Please try again."
    
    # Format response
    final_response = respondToUser(user_sentence, result)
    return final_response

def replace_spelled_numbers(text):
    """Replace spelled-out numbers (one, two, etc.) with digits in text"""
    number_words = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
        'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
        'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
        'twenty': 20
    }
    
    words = text.split()
    new_words = []
    for word in words:
        clean = word.lower().strip("''s")
        if clean in number_words:
            new_words.append(str(number_words[clean]))
        else:
            new_words.append(word)
    return ' '.join(new_words)

def safe_merge_team_names(sentence, known_teams):
    """Merge consecutive words that form a team name into a single entity"""
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

# Main execution block
if __name__ == "__main__":
    try:
        with open("questions.txt", "r") as f:
            user_sentence = f.read().strip()
        
        response = text_to_llm(user_sentence)
        print(response)
        print("Script executed successfully.")
    except Exception as e:
        print(f"Error in main execution: {e}")