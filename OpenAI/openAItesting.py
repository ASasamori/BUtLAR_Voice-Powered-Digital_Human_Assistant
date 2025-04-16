from openai import OpenAI

with open('api_key', 'r') as file:
    API_KEY = file.read()
client = OpenAI(api_key = API_KEY)
# Load the office hours information from a text file
with open('classes_taught', 'r') as file:
    classes_taught_content = file.read()

# Load the question from google ASR from a text file
with open('transcript', 'r') as file:
    user_question = file.read()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"The following are the office hours and courses being taught: {classes_taught_content}"},
        {
            "role": "user",
            "content": user_question
        }
    ]
)

print(completion.choices[0].message.content)