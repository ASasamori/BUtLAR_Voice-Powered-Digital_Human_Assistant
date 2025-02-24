# main.py
import data
import sqlite3

# Use a single database file for all tables
db_file = "school.db"

# Import CSV data into the same database file as separate tables
data.csv_to_sqlite('professors.csv', db_file, 'professors', encoding='utf-8-sig')
data.csv_to_sqlite('offerings.csv', db_file, 'offerings', encoding='utf-8-sig')
