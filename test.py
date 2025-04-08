import psycopg2

# Connection parameters
host = '35.184.0.202'

dbname = 'postgres'
user = 'postgres'
password = 'butlar'
port = '5432'

# Create a connection string
conn_string = f"host='{host}' dbname='{dbname}' user='{user}' password='{password}' port='{port}'"
try:
    # Attempt to connect to the database
    conn = psycopg2.connect(conn_string)
    print("Connection successful!")

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Execute a simple query to verify the connection
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print("Database version:", db_version)

    # Close the cursor and connection
    cursor.close()
    conn.close()

except Exception as e:
    print("Unable to connect to the database.")
    print(f"Error: {e}")