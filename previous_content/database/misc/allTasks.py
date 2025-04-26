# EC 463 Senior Design Digital Human Project
# Suhani Mitra - Combined Script for LangChain with Google Cloud SQL and Vertex AI

from langchain_google_cloud_sql_pg import PostgresLoader, PostgresEngine, Column
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_cloud_sql_pg import PostgresVectorStore, PostgresChatMessageHistory
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_core.prompts import PromptTemplate
import uuid

# Define variables
project_id = "sanguine-orb-441020-p6"
instance_name = "langchain-quickstart-instance"
region = "us-central1"
database_name = "ec463-temp-database"
password = "ec463"  # Replace with your actual password

# Initialize Postgres Engine
def setup_postgres_engine():
    return PostgresEngine.from_instance(
        project_id=project_id,
        instance=instance_name,
        region=region,
        database=database_name,
        user="postgres",
        password=password,
    )


# Use Case 1: Cloud SQL for PostgreSQL as Document Loader
async def load_documents(pg_engine, table_name="netflix_titles", content_columns=None):
    if content_columns is None:
        content_columns = ["title", "director", "cast", "description"]
    loader = await PostgresLoader.create(
        engine=pg_engine,
        query=f"SELECT * FROM {table_name};",
        content_columns=content_columns,
    )
    documents = await loader.aload()
    print(f"Loaded {len(documents)} documents.")
    return documents


# Use Case 2: Cloud SQL for PostgreSQL as Vector Store
def setup_vector_store(pg_engine, documents):
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
        overwrite_existing=True,
    )
    embeddings_service = VertexAIEmbeddings(model_name="textembedding-gecko@003", project=project_id)
    vector_store = PostgresVectorStore.create_sync(
        engine=pg_engine,
        embedding_service=embeddings_service,
        table_name=sample_vector_table_name,
        metadata_columns=[
            "show_id", "type", "country", "date_added", "release_year", "duration", "listed_in"
        ],
    )
    ids = [str(uuid.uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents, ids)

# Use Case 3: Cloud SQL for PostgreSQL as Chat Memory
def setup_chat_memory(pg_engine, session_id="my-test-session"):
    message_table_name = "message_store"
    pg_engine.init_chat_history_table(table_name=message_table_name)
    chat_history = PostgresChatMessageHistory.create_sync(pg_engine, session_id=session_id, table_name=message_table_name)
    return chat_history

# Final Conversational RAG Chain
def setup_rag_chain(pg_engine, chat_history):
    prompt = PromptTemplate(
        template="""Use all the information from the context and the conversation history to answer new question...
                    (Additional prompt details)""",
        input_variables=["context", "question", "chat_history"],
    )
    condense_question_prompt_passthrough = PromptTemplate(
        template="""Repeat the following question:
        {question}
        """, input_variables=["question"]
    )
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 5, "lambda_mult": 0.8})
    llm = VertexAI(model_name="gemini-pro", project=project_id)
    memory = ConversationSummaryBufferMemory(
        llm=llm,
        chat_memory=chat_history,
        output_key="answer",
        memory_key="chat_history",
        return_messages=True,
    )
    rag_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        verbose=False,
        memory=memory,
        condense_question_prompt=condense_question_prompt_passthrough,
        combine_docs_chain_kwargs={"prompt": prompt},
    )
    return rag_chain

# Main execution function
async def main():
    pg_engine = setup_postgres_engine()
    documents = await load_documents(pg_engine)
    setup_vector_store(pg_engine, documents)
    chat_history = setup_chat_memory(pg_engine)
    rag_chain = setup_rag_chain(pg_engine, chat_history)

    # Example questions
    questions = ["What movie was Brad Pitt in?", "How about Johnny Depp?", "Are there movies about animals?"]
    for q in questions:
        answer = rag_chain({"question": q, "chat_history": chat_history})["answer"]
        print(f"Question: {q}\nAnswer: {answer}\n")

# Run the main function if this is the main module
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
