import json
from openai import OpenAI
from textwrap import shorten
from collections import defaultdict
from datetime import datetime


# Load your API key safely
client = OpenAI(api_key="API KEY")

with open("questions.txt") as qfile:
    question = qfile.read().strip()

with open("BUECEClasses_SP2025_cleaned.json") as f:
    data = json.load(f)

courses = data["New item - 2"]["classes"]

course_groups = defaultdict(list)
for course in courses:
    subject = course["subject"]
    if subject.startswith("ENG"):
        subject = subject[3:]
    key = f"{subject} {course['catalog_nbr']}"
    course_groups[key].append(course)

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
    if component in ["lec", "lecture"]:
        return "lecture"
    elif component in ["lab", "laboratory"]:
        return "lab"
    elif component in ["dis", "discussion"]:
        return "discussion"
    return component

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
    return ("who teaches" in q or "which courses" in q or "what courses" in q or "professor" in q)

def summarize_course_for_question(question):
    summary = []
    requested_type = get_requested_section_type(question)

    # Handle case: "what courses does [professor] teach?"
    if is_professor_question(question):
        professor_courses = []
        seen = set()
        for section_list in course_groups.values():
            for sec in section_list:
                for instructor in sec.get("instructors", []):
                    name = instructor.get("name", "").lower()
                    if name and name in question.lower():
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

course_summaries = summarize_course_for_question(question)
course_info_string = "\n".join(course_summaries)

def ask_question(question):
    prompt = f"""You are an assistant who answers questions about Boston University ECE Spring 2025 courses.
Answer using ONLY the course info provided below. Do not guess or make up any details not in the list.

{shorten(course_info_string, width=12000, placeholder="...")}

Q: {question}
A:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content

print(ask_question(question))

