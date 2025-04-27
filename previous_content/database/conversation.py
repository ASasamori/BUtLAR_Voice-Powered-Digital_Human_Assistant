from langchain_google_vertexai import VertexAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_google_cloud_sql_pg import Column
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_cloud_sql_pg import PostgresVectorStore, PostgresChatMessageHistory, PostgresLoader, PostgresEngine, Column

import asyncio, uuid

# case 1
project_id_init="sanguine-orb-441020-p6"
instance_init="langchain-quickstart-instance"
region_init="us-central1"
database_init="ec463-temp-database"
user_init="postgres"
password_init="ec463"

pg_engine = PostgresEngine.from_instance(
    project_id=project_id_init,
    instance=instance_init,
    region=region_init,
    database=database_init,
    user=user_init,
    password=password_init,
)

table_name = "netflix_titles"
content_columns = ["title", "director", "cast", "description"]
documents=[]

# Wrap the code in an async function
async def load_documents():
    global documents
    loader = await PostgresLoader.create(
        engine=pg_engine,
        query=f"SELECT * FROM {table_name} LIMIT 1000;",
        content_columns=content_columns,
    )

    # documents = await loader.aload()
    # print(f"Loaded {len(documents)} from the database. 5 Examples:")
    # for doc in documents[:5]:
    #     print(doc)
    return await loader.aload()


# Run the async function
documents = asyncio.run(load_documents())


# case 2
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
    model_name="textembedding-gecko@003", project=project_id_init
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

# Look into this
docs_to_load = documents
# print(f"documents is {docs_to_load}")

# ! Uncomment the following line to load all 8,800+ documents to the database vector table with calling the embedding service.
# docs_to_load = documents

ids = [str(uuid.uuid4()) for i in range(len(docs_to_load))]

# print(f"Embedding documents: {docs_to_load}")
vector_store.add_documents(docs_to_load, ids)



# case 3
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


llm = VertexAI(model_name="gemini-pro", project=project_id_init)


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

q = "What movie was Brad Pitt in?" # replace with ASR output text that is a parameter to when this file is called
ans = rag_chain({"question": q, "chat_history": chat_history})["answer"]
print(f"Question: {q}\nAnswer: {ans}\n")

# q = "How about Jonny Depp?"
# ans = rag_chain({"question": q, "chat_history": chat_history})["answer"]
# print(f"Question: {q}\nAnswer: {ans}\n")

# q = "Are there movies about animals?"
# ans = rag_chain({"question": q, "chat_history": chat_history})["answer"]
# print(f"Question: {q}\nAnswer: {ans}\n")

# browser the chat history
chat_history.messages