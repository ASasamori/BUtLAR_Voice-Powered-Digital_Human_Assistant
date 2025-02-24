import sqlite3
import csv

def csv_to_sqlite(csv_file, db_file, table_name, encoding='utf-8-sig'):
    """Imports a CSV file into an SQLite database.
    
    Args:
        csv_file (str): Path to the CSV file.
        db_file (str): Path to the SQLite database file.
        table_name (str): Name of the table to create or replace.
        encoding (str): Encoding for reading the CSV (default: 'utf-8-sig' to handle BOM).
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    with open(csv_file, 'r', newline='', encoding=encoding) as file:
        reader = csv.reader(file)
        headers = next(reader)  # Read column names
        
        # Clean headers in case of BOM (though utf-8-sig should handle this)
        headers = [col.strip('\ufeff') for col in headers]
        
        cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        cursor.execute(f'CREATE TABLE {table_name} ({", ".join([f"{col} TEXT" for col in headers])})')
        
        for row in reader:
            placeholders = ', '.join(['?'] * len(row))
            cursor.execute(f'INSERT INTO {table_name} VALUES ({placeholders})', row)
    
    conn.commit()
    conn.close()