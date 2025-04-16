# json_to_sqlite.py (updated to include day, time, and room)
import json
import sqlite3

# Load JSON data
with open("BUECEClasses_SP2025_cleaned.json") as f:
    data = json.load(f)
    classes = data.get("New item - 2", {}).get("classes", [])

# Connect to SQLite database
conn = sqlite3.connect("school.db")
cursor = conn.cursor()

# Create table
cursor.execute("DROP TABLE IF EXISTS classes")
cursor.execute("""
CREATE TABLE classes (
    subject TEXT,
    catalog_nbr TEXT,
    crse_id TEXT,
    descr TEXT,
    component TEXT,
    class_section TEXT,
    start_dt TEXT,
    end_dt TEXT,
    class_nbr TEXT,
    instructors TEXT,
    campus_descr TEXT,
    days TEXT,
    time TEXT,
    room TEXT
)
""")

# Insert data
for c in classes:
    instructors = ", ".join(instr["name"] for instr in c.get("instructors", []))
    meetings = c.get("meetings", [])
    if meetings:
        meeting = meetings[0]
        days = meeting.get("days", "")
        start_time = meeting.get("start_time", "")
        end_time = meeting.get("end_time", "")

        def convert_time(raw):
            try:
                hour, minute, *_ = map(int, raw.split(".")[:2])
                suffix = "AM" if hour < 12 else "PM"
                hour = hour if 1 <= hour <= 12 else hour % 12 or 12
                return f"{hour}:{minute:02d} {suffix}"
            except:
                return ""

        formatted_time = f"{convert_time(start_time)} - {convert_time(end_time)}"
        time = formatted_time
        room = meeting.get("facility_id", "")
    else:
        days = ""
        time = ""
        room = ""

    row = (
        c.get("subject"),
        c.get("catalog_nbr"),
        c.get("crse_id"),
        c.get("descr"),
        c.get("component"),
        c.get("class_section"),
        c.get("start_dt"),
        c.get("end_dt"),
        c.get("class_nbr"),
        instructors,
        c.get("campus_descr"),
        days,
        time,
        room
    )
    cursor.execute("""
        INSERT INTO classes (
            subject, catalog_nbr, crse_id, descr, component,
            class_section, start_dt, end_dt, class_nbr,
            instructors, campus_descr, days, time, room
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)

conn.commit()
conn.close()
print("school.db successfully created with 'classes' table including days, time, and room.")
