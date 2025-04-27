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

# ------------------------------------------------------------------------------
# Universal Initialization (works for ANY dataset)
# ------------------------------------------------------------------------------

def initialize_components(config_path: str, table_name: str = "universal_dataset"):
    """Initialize once for any dataset. Requires:
    - A table with 'id', 'content', 'embedding' columns
    - Other columns treated as metadata (no indexes needed)"""
    with open(config_path, 'r') as f:
        config = json.load(f)
    # cloud_project_info = config["cloud_project_info"]
    cloud_project_info = config.get('cloud_project_info_2')


    # 1. Connect to PostgreSQL
    engine = PostgresEngine.from_instance(  
        project_id = cloud_project_info.get('project_id'),
        instance = cloud_project_info.get('instance_name'),
        region = cloud_project_info.get('region'),
        database = cloud_project_info.get('database_name'),
        user="postgres",
        password = cloud_project_info.get('password')
    )

    # 2. Initialize embedding model (works for any text)
    embeddings = VertexAIEmbeddings(
        model_name="textembedding-gecko@latest",
        project = cloud_project_info.get('project_id')
    )

    # Update the initialization of PostgresVectorStore
    # Try explicitly specifying the arguments
    return PostgresVectorStore.create_sync(
        engine=engine,
        table_name=table_name,
        metadata_columns=["show_id", "type", "country", "date_added", "release_year"],
        embedding_service=embeddings
        # embedding_function=embeddings  # Another potential variation
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('key_info')
    args = parser.parse_args()

    # Point to your dataset table (configured in DB)
    vector_store = initialize_components(args.key_info, table_name="movie_vector_table")
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    question = "Which movie is Tom Holland in?"
    results = vector_store.get_relevant_documents(question)
    print(f"Answer to: '{question}'")
    for idx, doc in enumerate(results, 1):
        print(f"{idx}. {doc.page_content}")
        print(f"   Metadata: {doc.metadata}\n")
    
    # process_query(vector_store, args.input_file, args.output_file)