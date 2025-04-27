from langchain_google_cloud_sql_pg import Column
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_cloud_sql_pg import PostgresVectorStore

import uuid

from case1 import documents, pg_engine, project_id_init

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

docs_to_load = documents[:5]

# ! Uncomment the following line to load all 8,800+ documents to the database vector table with calling the embedding service.
# docs_to_load = documents

ids = [str(uuid.uuid4()) for i in range(len(docs_to_load))]
vector_store.add_documents(docs_to_load, ids)


# See shell file for this part\

# # Import the netflix titles with vector table using gcloud command
# import_command_output = !gcloud sql import sql {instance_name} gs://cloud-samples-data/langchain/cloud-sql/postgres/netflix_titles_vector_table.sql --database={database_name} --quiet

# if "Imported data" in str(import_command_output):
#     print(import_command_output)
# elif "already exists" in str(import_command_output):
#     print("Did not import because the table already existed.")
# else:
#     raise Exception(f"The import seems failed:\n{import_command_output}")