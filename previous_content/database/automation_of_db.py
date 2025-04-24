import pandas as pd
from sqlalchemy import create_engine

# Load dataset
# df = pd.read_csv("your_dataset.csv")  # Or pd.read_json("your_dataset.json")
df = pd.read_json("test.json")

# Connect to PostgreSQL
# engine = create_engine("postgresql://postgres:butlar@localhost:5432/postgres")
engine = create_engine("postgresql://postgres:butlar@34.27.231.52:5432/postgres")

# Upload DataFrame to PostgreSQL (Automatically creates table!)
df.to_sql("test_table_does_this_work", engine, if_exists="replace", index=False)

print("Data uploaded successfully!")