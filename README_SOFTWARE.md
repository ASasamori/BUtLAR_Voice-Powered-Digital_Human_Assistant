# 

• A flow chart indicating the dependencies between these functions. For instance, if you have a
main.py and LCD.py, you need to show that LCD.py is a module used by main.py.

• Dev/build tool information: Package name and version info. For example, OpenCV 4.0.3 with
Python 3.8.1, using CUDA Toolbox 10.0 and GCC 9.1 and CMake 3.14.2

• How to install the project software stack from scratch (a blank hard drive / cloud instance) Please
provide concise documentation on what installation software is needed, and how to build from
source to binary as applicable. 

Personal Usage:
I followed this guide for creating and hosting the Postgres Database. The database looks like this:


Software Modules:

/Audio/testing_audio/intialize_database.ipynb
/Audio/testing_audio/test.py
/Audio/testing_audio/voiceAssistant_vanna.py

/Audio/testing_audio/django_top


Customer Usage
https://cloud.google.com/python/docs/setup
gcloud config set project [PROJECT_ID]


Steps to Download Google Cloud Service Account JSON Key:
	1.	Go to Google Cloud Console
→ https://console.cloud.google.com/
	2.	Select the correct project
(Make sure you select your project like sanguine-orb-441020-p6 in the dropdown at the top)
	3.	Navigate to IAM & Admin → Service Accounts
	•	On the left sidebar, click IAM & Admin
	•	Then click Service Accounts
	4.	Create a new Service Account (if you don’t already have one)
	•	Click + CREATE SERVICE ACCOUNT at the top.
	•	Give it a name (e.g., butlar-service-account), description (optional).
	•	Click CREATE AND CONTINUE.
	5.	Grant this service account roles
	•	You must assign it at least enough permissions.
	•	Typical permissions for database projects:
	•	Cloud SQL Admin (for Postgres)
	•	Storage Admin (if using GCS buckets)
	•	Viewer (for basic access)
	•	Then click DONE.
	6.	Download the Key (JSON)
	•	Find the newly created Service Account in the list.
	•	Click on the email name of the Service Account.
	•	Go to the Keys tab.
	•	Click ADD KEY → Create new key.
	•	Choose JSON.
	•	Click Create → It will automatically download a .json file to your computer.


export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

    


Using python 3.12.0 right now. Download everything from the requirements.txt file.
Use the https://vanna.ai/
and check the different versions you can use:
Databases: Postgres, Microsoft SQL Server, MySQL, DuckDB, Snowflake, BigQuery, SQLite, Oracle, other SQL generated database
LLM: OpenAI, Ollama, Azure OpenAI, Google Gemini, Anthropic, Mistral via Mistral API
Metadata Storage: ChromaDB, Qdrant, Marquo, or other VectorDBs (requires additional setup)
Use OpenAI API key, and add to environment variable.
Initalize Google Cloud environment to your machine, via this:
Use the intialize_database.ipynb file to configure API key and model

Note that the information only applies to the PostGres database. There was not enough time/information to the other methods. Additionally, just using ChromaDB for metadata storage. 

Change the information so that the host is available.
<!-- vn.connect_to_postgres(host='35.226.19.55', dbname='ece_day_db', user='postgres', password='butlar', port='5432') -->

Add documentation from Vanna or other information that is easily parsable by the database

Use information such as:
<!-- 

# The information schema query may need some tweaking depending on your database. This is a good starting point.
df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")

# This will break up the information schema into bite-sized chunks that can be referenced by the LLM
plan = vn.get_training_plan_generic(df_information_schema)
plan

# If you like the plan, then uncomment this and run it to train
# vn.train(plan=plan)



# The following are methods for adding training data. Make sure you modify the examples to match your database.

# DDL statements are powerful because they specify table names, colume names, types, and potentially relationships
vn.train(ddl="""
    CREATE TABLE IF NOT EXISTS my-table (
        id INT PRIMARY KEY,
        name VARCHAR(100),
        age INT
    )
""")

# Sometimes you may want to add documentation about your business terminology or definitions.
vn.train(documentation="Our business defines OTIF score as the percentage of orders that are delivered on time and in full")

# You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.
vn.train(sql="SELECT * FROM my-table WHERE name = 'John Doe'") -->



## Frontend

*Our frontend implentation is extremeley basic, it has just been implemented for voice activation and displaying the raw backend architecture.*

---

[urls.py](Audio/testing_audio/django_top/butlar/urls.py) (part of the Django framework) does the URL forwarding to preload the information to the user.

---

[consumers.py](Audio/testing_audio/django_top/butlar/consumers.py) manages real-time communication between the Django frontend and the voice assistant backend using WebSockets.
When a user connects, it spawns a new thread that launches the audio capture and processing pipeline through a shell command. This subprocess streams microphone input into a pipeline involving ```miniaudio_stream```, ```sox```, and ```main.py```. ```miniaudio_stream``` is an executable that was created using a simple ```C``` file. Here is the main loop of [miniaudio_stream.c](Audio/testing_audio/miniaudio_stream.c):
```c
    // Start device
    result = ma_device_start(&device);
    if (result != MA_SUCCESS) {
        fprintf(stderr, "Failed to start device\n");
        ma_device_uninit(&device);
        ma_context_uninit(&context);
        return -1;
    }

    // Run until signal received
    while (running) {
        ma_sleep(100);
        
    }

    // Cleanup
    ma_device_uninit(&device);
    ma_context_uninit(&context);
    return 0;
```

Inside the subprocess loop, the consumer reads lines of output and categorizes them into types: transcripts, responses, or status updates. These are sent back to the frontend through the WebSocket. For instance, when a final transcript is recognized:

```python
if text.startswith("Final transcript:"):
    payload = {"type": "transcript", "text": text.replace("Final transcript:", "").strip()}
```

The consumer also listens for control messages from the frontend, such as "pause" or "resume", and updates internal flags accordingly. This controls when the backend should stop listening (during TTS playback) or start listening again. This is done by writing into simple flag files:


```python
with open(flag_file, "w") as f:
    f.write("responding")
```

---

[butlar_interface.html](Audio/testing_audio/django_top/butlar/templates/butlar/butlar_interface.html) provides the web-based user interface for interacting with BUtLAR.
It establishes a WebSocket connection to the backend when the user clicks “Start,” and dynamically displays messages and system status updates in a chat-style window.

When a transcript or a final response is received from the backend, it updates the chat window and speaks the response using the browser’s SpeechSynthesis API:

```javascript
const utterance = new SpeechSynthesisUtterance(data.text);
speechSynthesis.speak(utterance);
```

During TTS playback, the frontend sends a "pause" message to the backend to prevent accidental audio capture, and a "resume" message when speaking finishes:

```javascript
socket.send(JSON.stringify({ type: "pause", duration: estimatedDurationSec }));
```

The UI also updates a visible status bar to reflect current activities — whether the system is listening, processing, or speaking — providing clear feedback to the user.


<!-- vn = MyVanna(config={'api_key': api_key, 'model': 'gpt-3.5-turbo'})

# FIXME: The dbname is always dynamic!
vn.connect_to_postgres(host='35.226.19.55', dbname='ece_day_db', user='postgres', password='butlar', port='5432') -->

## Backend

[main.py](Audio/testing_audio/main.py) calls the ```process_audio_stream()``` function from voiceAssistant.py. It is called by the django backend.

---

[fullDatabaseRetrieval.py](Audio/testing_audio/fullDatabaseRetrieval.py) loads course information from a local JSON file and handles natural language questions by matching key attributes such as course code, meeting time, location, or instructor name. Corrects professor names using an OpenAI LLM call if there are typos or phonetic variations. Parses and matches the corrected question against the available course dataset. Matches course codes (e.g., “EC 413”), section types, and instructor names. Handles structured breakdowns for different question types (e.g., “when”, “where”, “who teaches”). Formats a prompt that contains only valid course data, instructing the LLM to answer strictly based on the provided information.

```
You are an assistant answering BU course questions using ONLY this data: [course info]...
Q: [user question]
A:
```

Asking a question through the OpenAI API is the most important response for the prompt engineering section.

```python
def ask_question(question):
    with open(COURSE_DATA_FILE) as f:
        data = json.load(f)
    courses = data["New item - 2"]["classes"]

    course_info_string = "\n".join(summarize_course_for_question(question, courses))

    prompt = f"""
    You are an assistant answering BU course questions using ONLY this data:
    {shorten(course_info_string, width=12000, placeholder="...")}

    Q: {question}
    A:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content
```

Professor names in questions are corrected by matching against a known instructor list, handled by a dedicated LLM prompt.

```python
def correct_last_name(question):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a precise name-matching assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0.1,
    )
    return corrected if corrected else question
```

---

[voiceAssistant.py](Audio/testing_audio/voiceAssistant.py) streams live audio input to Google Cloud Speech-to-Text using the StreamingRecognizeRequest API. Audio is captured at 16 kHz, mono channel, 16-bit samples. The script also uses ```StreamingRecognizeRequest ``` configuration. In this way, there is automatic punctuation and interim results.

Whenever the assistant is about to speak — for example, when it generates a TTS response based on a completed question — it writes a temporary flag indicating that it is “responding.” During this period, instead of reading real audio from the microphone, the generator deliberately produces silent audio chunks, made up of zero bytes. This allows the streaming connection to remain active, because Google’s API expects continuous audio, but it prevents the assistant’s own voice from being captured. Here, the silence injection is handled simply by yielding:

```py 
yield StreamingRecognizeRequest(audio_content=silent_chunk)
```

Once the assistant finishes speaking, the system transitions back into listening mode. However, there is an important detail to avoid capturing any residual audio that may still exist in the microphone buffer. Before resuming normal capture, the code flushes a large number of audio chunks — effectively discarding several seconds’ worth of stale or leftover audio — ensuring that when the microphone is live again, it captures only fresh user speech and not echoes of the assistant itself. The flushing mechanism reads and discards audio from stdin in a loop:

```py
for _ in range(flush_chunks):
    _ = sys.stdin.buffer.read(4096)
```

## Database
[school.db](Audio/testing_audio/sql_database/school.db) is the database that loads our data. For ease, here are what the rows look like:
![](images/school_db.png)



<!-- Our database is running on a simple Postgres server hosted by Google Cloud Compute Engine. The chepaest option is being used, which is **e2-micro instance**. -->