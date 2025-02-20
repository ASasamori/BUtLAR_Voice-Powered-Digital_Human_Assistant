# main.py
import data
import sqlite3

# Use a single database file for all tables
db_file = "school.db"

# Import CSV data into the same database file as separate tables
data.csv_to_sqlite('professors.csv', db_file, 'professors')
data.csv_to_sqlite('offerings.csv', db_file, 'offerings')

# get a text file

courseName = "Machine Learning"

sql_query = f"""
SELECT p."Room"
FROM offerings o
JOIN professors p ON o."Last" = p."Last"
WHERE o."Name" LIKE '%{courseName}%';
"""

# Connect to the database and execute the query
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

try:
    cursor.execute(sql_query)
    results = cursor.fetchall()
    print("Query Results:")
    for row in results:
        print(row)
except Exception as e:
    print("Error executing query:", e)
finally:
    conn.close()
