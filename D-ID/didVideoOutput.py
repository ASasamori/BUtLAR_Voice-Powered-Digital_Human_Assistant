import requests
import time
import base64

# Define API endpoint and credentials
url = "https://api.d-id.com/talks"


with open('user.txt', 'r') as f:
    user = f.read()
with open('password.txt', 'r') as f:
    password = f.read()

# Encode credentials in Base64 for Basic Auth
auth_string = f"{user}:{password}"
encoded_auth = base64.b64encode(auth_string.encode()).decode()

# Define headers
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Basic {encoded_auth}"  # Adjust if using Bearer token instead
}
with open('transcript.txt', 'r') as f:
    transcript = f.read()
# Define payload
payload = {
    "source_url": "https://easy-peasy.ai/cdn-cgi/image/quality=80,format=auto,width=700/https://fdczvxmwwjwpwbeeqcth.supabase.co/storage/v1/object/public/images/1dbb9693-4e22-48fd-821d-8120b1ac3aca/5f2d5cdd-6fa4-412d-a0a7-04177bf592c9.png",
    "script": {
        "type": "text",
        "input": transcript,
    }
}

try:
    # Step 1: POST to create a talk
    print("Creating talk...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
        data = response.json()
        talk_id = data.get("id")
        print(f"Talk created successfully. ID: {talk_id}")
    else:
        print(f"Failed to create talk. Status Code: {response.status_code}, Response: {response.text}")
        exit()

    # Step 2: Poll the GET endpoint to check the status and retrieve the result
    get_url = f"https://api.d-id.com/talks/{talk_id}"
    print("Polling for video readiness...")

    while True:
        get_response = requests.get(get_url, headers=headers)
        if get_response.status_code == 200:
            get_data = get_response.json()
            status = get_data.get("status")

            if status == "done":
                result_url = get_data.get("result_url")
                print(f"Video is ready! Access it at: {result_url}")
                break
            elif status in ["created", "started"]:
                print("Video processing... Waiting 5 seconds before checking again.")
                time.sleep(5)
            else:
                print(f"Unknown status: {status}. Full response: {get_data}")
                break
        else:
            print(
                f"Failed to fetch talk status. Status Code: {get_response.status_code}, Response: {get_response.text}")
            break

except Exception as e:
    print(f"An error occurred: {e}")
