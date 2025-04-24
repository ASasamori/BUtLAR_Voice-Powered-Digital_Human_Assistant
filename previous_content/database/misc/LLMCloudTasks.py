# https://colab.research.google.com/github/googleapis/langchain-google-cloud-sql-pg-python/blob/main/samples/langchain_quick_start.ipynb#scrollTo=vHdR4fF3vLWA
# Source code for the above link
# Compiling the various steps into one script
# Suhani Mitra
# 11/14/2024
# EC 463 Senior Design Digital Human Project

from langchain_google_cloud_sql_pg import PostgresLoader, PostgresEngine, Column
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_cloud_sql_pg import PostgresVectorStore, PostgresChatMessageHistory, PostgresEngine
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import PromptTemplate

import uuid

# @markdown Please fill in the value below with your GCP project ID and then run the cell.

# Please fill in these values.
project_id = "sanguine-orb-441020-p6"# @param {type:"string"}

# Quick input validations.
assert project_id, "⚠️ Please provide a Google Cloud project ID"

# Configure gcloud.
!gcloud config set project {project_id}

# Setup the PostgresEngine

project_id="sanguine-orb-441020-p6"
instance="langchain-quickstart-instance"
region="us-central1"
database="ec463-temp-database"
user="postgres"
password="*****"

pg_engine = PostgresEngine.from_instance(
    project_id=project_id,
    instance=instance,
    region=region,
    database=database,
    user=user,
    password=password,
)

# Use Case 1: Cloud SQL for PostgreSQL as a document loader

table_name = "netflix_titles"
content_columns = ["title", "director", "cast", "description"]
loader = await PostgresLoader.create(                 # causing errors
    engine=pg_engine,
    query=f"SELECT * FROM {table_name};",
    content_columns=content_columns,
)

documents = await loader.aload()
print(f"Loaded {len(documents)} from the database. 5 Examples:")
for doc in documents[:5]:
    print(doc)

  
# Use Case 2: Cloud SQL for PostgreSQL as Vector Store
sample_vector_table_name = "movie_vector_table_samples"

pg_engine.init_vectorstore_table(
    sample_vector_table_name,
    vector_size=768,
    metadata_columns=[
        Column("show_id", "VARCHAR", nullable=True),
        Column("type", "VARCHAR", nullable=True),
        Column("country", "VARCHAR", nullable=True),
        Column("date_added", "VARCHAR", nullable=True),
        Column("release_year", "INTEGER", nullable=True),
        Column("rating", "VARCHAR", nullable=True),
        Column("duration", "VARCHAR", nullable=True),
        Column("listed_in", "VARCHAR", nullable=True),
    ],
    overwrite_existing=True,  # Enabling this will recreate the table if exists.
)

# Initialize the embedding service. In this case we are using version 003 of Vertex AI's textembedding-gecko model. In general, it is good practice to specify the model version used.
embeddings_service = VertexAIEmbeddings(
    model_name="textembedding-gecko@003", project=project_id
)

vector_store = PostgresVectorStore.create_sync(
    engine=pg_engine,
    embedding_service=embeddings_service,
    table_name=sample_vector_table_name,
    metadata_columns=[
        "show_id",
        "type",
        "country",
        "date_added",
        "release_year",
        "duration",
        "listed_in",
    ],
)

docs_to_load = documents[:5]

# ! Uncomment the following line to load all 8,800+ documents to the database vector table with calling the embedding service.
# docs_to_load = documents
ids = [str(uuid.uuid4()) for i in range(len(docs_to_load))]
vector_store.add_documents(docs_to_load, ids)

# Import the netflix titles with vector table using gcloud command
import_command_output = !gcloud sql import sql {instance_name} gs://cloud-samples-data/langchain/cloud-sql/postgres/netflix_titles_vector_table.sql --database={database_name} --quiet

# above line causing errors

if "Imported data" in str(import_command_output):
    print(import_command_output)
elif "already exists" in str(import_command_output):
    print("Did not import because the table already existed.")
else:
    raise Exception(f"The import seems failed:\n{import_command_output}")



# Use case 3: Cloud SQL for PostgreSQL as Chat Memory

message_table_name = "message_store"
pg_engine.init_chat_history_table(table_name=message_table_name)

chat_history = PostgresChatMessageHistory.create_sync(
    pg_engine,
    session_id="my-test-session",
    table_name=message_table_name,
)

chat_history.add_user_message("Hi!")
chat_history.add_ai_message("Hello there. I'm a model and am happy to help!")

chat_history.messages

# FINAL: Conversational RAG Chain backed by Cloud SQL Postgre

# Initialize the embedding service
embeddings_service = VertexAIEmbeddings(
    model_name="textembedding-gecko@latest", project=project_id
)


# Initialize the Vector Store
vector_table_name = "movie_vector_table"
vector_store = PostgresVectorStore.create_sync(
    engine=pg_engine,
    embedding_service=embeddings_service,
    table_name=vector_table_name,
    metadata_columns=[
        "show_id",
        "type",
        "country",
        "date_added",
        "release_year",
        "duration",
        "listed_in",
    ],
)

# Initialize the PostgresChatMessageHistory
chat_history = PostgresChatMessageHistory.create_sync(
    pg_engine,
    session_id="my-test-session",
    table_name="message_store",
)

# Prepare some prompt templates for the ConversationalRetrievalChain
prompt = PromptTemplate(
    template="""Use all the information from the context and the conversation history to answer new question. If you see the answer in previous conversation history or the context. \
Answer it with clarifying the source information. If you don't see it in the context or the chat history, just say you \
didn't find the answer in the given data. Don't make things up.

Previous conversation history from the questioner. "Human" was the user who's asking the new question. "Assistant" was you as the assistant:
```{chat_history}
```

Vector search result of the new question:
```{context}
```

New Question:
```{question}```

Answer:""",
    input_variables=["context", "question", "chat_history"],
)
condense_question_prompt_passthrough = PromptTemplate(
    template="""Repeat the following question:
{question}
""",
    input_variables=["question"],
)

# Initialize retriever, llm and memory for the chain
retriever = vector_store.as_retriever(
    search_type="mmr", search_kwargs={"k": 5, "lambda_mult": 0.8}
)

llm = VertexAI(model_name="gemini-pro", project=project_id)


chat_history.clear()

memory = ConversationSummaryBufferMemory(
    llm=llm,
    chat_memory=chat_history,
    output_key="answer",
    memory_key="chat_history",
    return_messages=True,
)

# create the ConversationalRetrievalChain
rag_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    verbose=False,
    memory=memory,
    condense_question_prompt=condense_question_prompt_passthrough,
    combine_docs_chain_kwargs={"prompt": prompt},
)

# ask some questions
q = "What movie was Brad Pitt in?"
ans = rag_chain({"question": q, "chat_history": chat_history})["answer"]
print(f"Question: {q}\nAnswer: {ans}\n")

q = "How about Jonny Depp?"
ans = rag_chain({"question": q, "chat_history": chat_history})["answer"]
print(f"Question: {q}\nAnswer: {ans}\n")

q = "Are there movies about animals?"
ans = rag_chain({"question": q, "chat_history": chat_history})["answer"]
print(f"Question: {q}\nAnswer: {ans}\n")

# browser the chat history
chat_history.messages