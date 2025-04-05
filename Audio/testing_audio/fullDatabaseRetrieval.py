import json
from openai import OpenAI
from textwrap import shorten
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import os
import re

# PATH SETUP: Get the directory of this script
script_dir = Path(__file__).resolve().parent

# Load API key from .env file
dotenv_path = script_dir / '../../.env'  # Adjust path to match your structure
load_dotenv(dotenv_path=dotenv_path)
open_ai_api_key = os.getenv("open_ai_api_key")
if not open_ai_api_key:
    raise ValueError("OpenAI API key not found in .env file")

# Initialize OpenAI client
client = OpenAI(api_key=open_ai_api_key)

# File path for course data
COURSE_DATA_FILE = "database/BUECEClasses_SP2025.json"


day_lookup = {
    "Mo": "Mondays", "Tu": "Tuesdays", "We": "Wednesdays",
    "Th": "Thursdays", "Fr": "Fridays", "Sa": "Saturdays", "Su": "Sundays"
}

def format_days(days_str):
    days = [days_str[i:i+2] for i in range(0, len(days_str), 2)]
    return " and ".join([day_lookup.get(d, d) for d in days])

def format_time(tstr):
    try:
        clean = tstr.replace(".", ":").split(":")
        fixed = f"{clean[0]}:{clean[1]}:00"
        dt = datetime.strptime(fixed, "%H:%M:%S")
        return dt.strftime("%I:%M").lstrip("0")
    except:
        return tstr

def normalize_component(component):
    component = component.strip().lower()
    return {
        "lec": "lecture", "lecture": "lecture",
        "lab": "lab", "laboratory": "lab",
        "dis": "discussion", "discussion": "discussion"
    }.get(component, component)

def get_requested_section_type(question):
    q = question.lower()
    if "lab" in q:
        return "lab"
    elif "discussion" in q:
        return "discussion"
    elif "lecture" in q:
        return "lecture"
    return None

def is_time_question(question):
    return any(kw in question.lower() for kw in ["when", "what time", "time", "schedule"])

def is_location_question(question):
    return any(kw in question.lower() for kw in ["where", "location", "room", "building"])

def is_professor_question(question):
    q = question.lower()
    return any(phrase in q for phrase in [
        "who teaches", "which courses", "which classes",
        "what courses", "what classes",
        "professor", "dr.", "instructor", "taught by"
    ])


def text_to_speech(text, output_file="text_to_speech_output.mp3"):
    """
    Convert text to speech using OpenAI's Text-to-Speech API
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",  # You can also use "tts-1-hd" for higher quality
            voice="onyx", 
            input=text,
        )
        
        # Save the audio file
        output_path = script_dir / output_file
        response.stream_to_file(output_path)
        return output_path
    except Exception as e:
        print(f"Error in text-to-speech conversion: {e}")
        return None


def correct_last_name(question):
    # Load instructor names database
    df = pd.read_csv(script_dir / "database/instructorNames.csv")
    
    # Create a comprehensive list of name variations
    name_variations = []
    for _, row in df.iterrows():
        first = row['FirstName'].lower()
        last = row['LastName'].lower()
        
        # Add standard variations
        name_variations.append({
            'correct_first': row['FirstName'],
            'correct_last': row['LastName'],
            'variations': [
                f"{first} {last}",
                f"{first[0]} {last}",
                f"{first} {last[0]}",
                last,  # Just last name
                first   # Just first name
            ]
        })
        
        # Handle special cases (like "Alexander (Sasha) Sergienko")
        if '(' in row['FirstName']:
            nickname = row['FirstName'].split('(')[1].split(')')[0].lower()
            name_variations.append({
                'correct_first': row['FirstName'],
                'correct_last': row['LastName'],
                'variations': [
                    f"{nickname} {last}",
                    nickname
                ]
            })

    # Prepare the prompt with specific examples
    examples = "\n".join([
        f"- '{var['correct_first']} {var['correct_last']}' can be matched to: {', '.join(var['variations'])}"
        for var in name_variations[:5]  # Show first 5 as examples
    ])
    
    prompt = f"""You are an expert at matching professor names with possible misspellings. Your task is to:
1. Analyze this question: "{question}"
2. Compare it against this database of professors (first 5 shown as examples):
{examples}
3. If a word closely resembles a name (e.g., typo or phonetic), replace it with the correct version. E.g. if there is a space between two words that could together sound like a name, please correct that.
4. For any name-like words in the question, find the closest match in our database
5. Return the corrected question with proper names

Special Rules:
- "Brian coulis" should become "Brian Kulis"
- Match even with minor typos or phonetic similarities
- Only correct names that match our database
- Return the original question if no clear match exists

Return ONLY the corrected question, nothing else."""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Using more powerful model for better accuracy
            messages=[
                {"role": "system", "content": "You are a precise name-matching assistant for university professors."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # Lower temperature for more deterministic results
        )
        
        corrected = completion.choices[0].message.content.strip()
        
        # Final verification - ensure the correction actually exists in our database
        corrected_names = re.findall(r'([A-Z][a-z]+ [A-Z][a-z\'\-]+)', corrected)
        if corrected_names:
            all_names = set(df['FirstName'] + ' ' + df['LastName'])
            for name in corrected_names:
                if name not in all_names:
                    return question  # Revert if correction isn't valid
                    
        return corrected if corrected else question
    
    except Exception as e:
        print(f"Error in name correction: {e}")
        return question


def summarize_course_for_question(question, courses):
    course_groups = defaultdict(list)
    for course in courses:
        subject = course["subject"]
        if subject.startswith("ENG"):
            subject = subject[3:]
        key = f"{subject} {course['catalog_nbr']}"
        course_groups[key].append(course)

    summary = []
    requested_type = get_requested_section_type(question)


     # Handle case: "what courses does [professor] teach?"
    if is_professor_question(question):
        professor_courses = []
        seen = set()
        for section_list in course_groups.values():
            for sec in section_list:
                for instructor in sec.get("instructors", []):
                    full_name = instructor.get("name", "").lower()
                    last_name = full_name.split()[-1] if full_name else ""
                    if full_name and (full_name in question.lower() or last_name in question.lower()):
                        subject = sec["subject"]
                        if subject.startswith("ENG"):
                            subject = subject[3:]
                        course_code = f"{sec['subject'].replace('ENG', '')} {sec['catalog_nbr']}"
                        course_title = sec.get("descr", "")
                        if course_code not in seen:
                            professor_courses.append(f"{course_code} - {course_title}")
                            seen.add(course_code)
        if professor_courses:
            return [f"This professor teaches:\n" + "\n".join(professor_courses)]
            

    for section_list in course_groups.values():
        subject = section_list[0]["subject"]
        if subject.startswith("ENG"):
            subject = subject[3:]
        course_code = f"{subject} {section_list[0]['catalog_nbr']}"
        course_title = section_list[0].get("descr", "")
        instructor_names = [i["name"].lower() for s in section_list for i in s.get("instructors", [])]
        user_question = question.lower()

        normalized_course_code = course_code.lower().replace(" ", "")
        normalized_question = user_question.replace(" ", "")

        if normalized_course_code not in normalized_question and course_title.lower() not in user_question:
            continue

        if is_professor_question(question):
            for sec in section_list:
                instructor = ", ".join(i['name'] for i in sec.get("instructors", [])) or "TBA"
                if normalized_course_code in normalized_question:
                    summary.append(f"The instructor for {course_code} is {instructor}.")
                    break
                elif any(name in user_question for name in instructor_names):
                    summary.append(f"{course_code} - {course_title}")
                    break
            continue

        matching_sections = []
        for s in section_list:
            section_type = normalize_component(s.get("component", ""))
            if requested_type:
                if section_type == requested_type:
                    matching_sections.append(s)
            else:
                matching_sections.append(s)

        if not matching_sections:
            if requested_type:
                summary.append(f"There is no information provided about the {course_code} {requested_type} schedule for Spring 2025.")
            continue

        for sec in matching_sections:
            section_type = normalize_component(sec.get("component", ""))
            if requested_type and section_type != requested_type:
                continue

            meetings = sec.get("meetings", [])
            raw_days = "".join(m.get('days', '') for m in meetings)
            days = format_days(raw_days)

            time_ranges = []
            for m in meetings:
                start_raw = m.get('start_time', '')
                end_raw = m.get('end_time', '')
                if start_raw and end_raw:
                    start_clean = format_time(start_raw)
                    end_clean = format_time(end_raw)
                    time_ranges.append(f"{start_clean} to {end_clean}")
            times = ", ".join(time_ranges) if time_ranges else "TBA"

            rooms = ", ".join(
                f"{m.get('bldg_cd', 'TBA')} {m.get('room', '')}".strip()
                for m in meetings if m.get('bldg_cd') and m.get('room')
            ) or "TBA"

            instructor = ", ".join(i['name'] for i in sec.get("instructors", []))

            if is_time_question(question):
                summary.append(f"{course_code} {section_type} is on {days} from {times}.")
            elif is_location_question(question):
                summary.append(f"{course_code} {section_type} is held in {rooms}.")
            else:
                summary.append(f"{course_code} {section_type} with {instructor} meets on {days} from {times} in {rooms}. Topic: {course_title}")

    if not summary:
        summary.append("No matching course section was found based on your question.")

    return summary

def ask_question(question):
    """Loads course data, processes it, and queries OpenAI."""
    with open(COURSE_DATA_FILE) as f:
        data = json.load(f)
    courses = data["New item - 2"]["classes"]
    
    course_summaries = summarize_course_for_question(question, courses)
    course_info_string = "\n".join(course_summaries)
    # print("course info string for debugging", course_info_string)

    prompt = f"""You are an assistant who answers questions about Boston University Spring 2025 courses.
Answer using ONLY the course info provided below. Do not guess or make up any details not in the list.

{shorten(course_info_string, width=12000, placeholder="...")}

Q: {question}
A:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content

def answer_course_question(question):
    """Single function to call when importing this file elsewhere."""
    corrected_question = correct_last_name(question)
    print(f"Processing question: '{corrected_question}'")
    # Convert response to speech and play it
    response_text = ask_question(corrected_question)

    # Text to Speech Conversion
    print("Converting response to speech...")
    audio_file = text_to_speech(response_text)
    print(f"Audio file saved to: {audio_file}")
    
    return response_text

if __name__ == "__main__":
    with open("questions.txt") as qfile:
        question = qfile.read().strip()
    print(answer_course_question(question))
