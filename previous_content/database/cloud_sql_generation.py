from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_google_cloud_sql_pg import (
    PostgresEngine,
    PostgresVectorStore,
    PostgresChatMessageHistory,
)
import json
from pathlib import Path
import argparse

# Input file information
parser = argparse.ArgumentParser()
parser.add_argument('input_file')
parser.add_argument('output_file')
parser.add_argument('key_info')
args = parser.parse_args()

with open(args.key_info, 'r') as f:
    config = json.load(f)

cloud_project_info = config.get('cloud_project_info')
project_id = cloud_project_info.get('project_id')
instance_name = cloud_project_info.get('instance_name')
region = cloud_project_info.get('region')
database_name = cloud_project_info.get('database_name')
password = cloud_project_info.get('password')

# Initialize the embedding service
embeddings_service = VertexAIEmbeddings(
    model_name="textembedding-gecko@latest", project=project_id
)

# Initialize the engine
pg_engine = PostgresEngine.from_instance(
    project_id=project_id,
    instance=instance_name,
    region=region,
    database=database_name,
    user="postgres",
    password=password,
)

# 
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

##########################################################
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

##########################################################
# Initialize retriever, llm and memory for the chain
retriever = vector_store.as_retriever(
    search_type="mmr", search_kwargs={"k": 5, "lambda_mult": 0.8}
)

llm = VertexAI(model_name="gemini-pro", project=project_id)

##########################################################
# chat_history.clear()

# TODO: Fix this Conversation Summary Buffer Memory later
memory = ConversationSummaryBufferMemory(
    llm=llm,
    chat_memory=chat_history,
    output_key="answer",
    memory_key="chat_history",
    return_messages=True,
)
##########################################################
# create the ConversationalRetrievalChain
rag_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    verbose=False,
    memory=memory,
    condense_question_prompt=condense_question_prompt_passthrough,
    combine_docs_chain_kwargs={"prompt": prompt},
)


with open(args.input_file, 'r') as file:
    user_question = file.read()

q = user_question
ans = rag_chain.invoke(
    {"question": q},
    config={"configurable": {"session_id": "my-test-session"}}
)["answer"]
# print(f"Question: {q}\nAnswer: {ans}\n")
with open(args.output_file, 'w') as output_file:
    output_file.write(ans)