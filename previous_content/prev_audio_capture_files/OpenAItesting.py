import argparse
from openai import OpenAI
import json
from pathlib import Path

# Function to handle the OpenAI API call and file handling
def process_transcript(input_file, output_file, database_and_keys):
    # Load key and database
    db_and_key_path = Path(database_and_keys)
    with db_and_key_path.open('r') as file:
        config = json.load(file)
    client = OpenAI(api_key=(config.get('openai_api_key')))
    classes_taught_content = config['classes_taught']

    # Load the user question (transcript) from the input file
    with open(input_file, 'r') as file:
        user_question = file.read()

    # Send the request to OpenAI API
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"The following are the office hours and courses being taught: {classes_taught_content}"},
            {"role": "user", "content": user_question}
        ]
    )

    # Get the response from OpenAI
    response_content = completion.choices[0].message.content

    # Write the response to the output file
    with open(output_file, 'w') as file:
        file.write(response_content)

    print(f"Response written to {output_file}")

# Set up argparse for command-line argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process transcript and output response")
    parser.add_argument("input_file", help="The input transcript file (e.g., ASR output)")
    parser.add_argument("output_file", help="The output file where the response will be written")
    parser.add_argument('database_and_keys', help="PATH: Database and key information")

    args = parser.parse_args()

    # Process the transcript
    process_transcript(args.input_file, args.output_file, args.database_and_keys)