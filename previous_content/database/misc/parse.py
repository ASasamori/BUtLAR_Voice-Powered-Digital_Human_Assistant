from flask import Flask, request, jsonify
from google.cloud import bigquery
import openai
import os

# Initialize Flask app
app = Flask(__name__)

# Set up your Google Cloud and OpenAI credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path_to_your_google_credentials.json"
openai.api_key = "YOUR_OPENAI_API_KEY"

# Initialize BigQuery client
bigquery_client = bigquery.Client()

def fetch_data_from_bigquery(query):
    """Fetches data from BigQuery based on a SQL query."""   
    query_job = bigquery_client.query(query)  # Run the query
    result = query_job.result()
    data = [dict(row) for row in result]  # Convert rows to a list of dictionaries
    return data

@app.route("/ask", methods=["POST"])
def ask():
    # Get user question from the request
    user_question = request.json["question"]

    # Define a query to fetch relevant data based on the question
    # (This is a simplified example; you can make this dynamic)
    # For example, here we assume the user is asking for sales data in October
    if "October" in user_question:
        query = "SELECT * FROM your_dataset.your_table WHERE month = 'October'"
    else:
        query = "SELECT * FROM your_dataset.your_table LIMIT 10"  # Default query

    # Fetch data from BigQuery
    data = fetch_data_from_bigquery(query)

    # Format the data for the prompt
    data_text = "\n".join([str(row) for row in data])

    # Create a prompt for OpenAI with the user question and data
    prompt = (
        f"The user wants to know: {user_question}\n\n"
        f"Here is the relevant data:\n{data_text}\n\n"
        "Based on this data, generate a helpful response."
    )

    # Call OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )

    # Extract and return the response text
    answer = response.choices[0].text.strip()
    return jsonify({"response": answer})

if __name__ == "__main__":
    app.run(debug=True)
