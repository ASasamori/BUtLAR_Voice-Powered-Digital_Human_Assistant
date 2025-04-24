from langchain_google_cloud_sql_pg import PostgresLoader, PostgresEngine, Column
import asyncio


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
documents = []

# Wrap the code in an async function
async def load_documents():
    loader = await PostgresLoader.create(
        engine=pg_engine,
        query=f"SELECT * FROM {table_name};",
        content_columns=content_columns,
    )

    documents = await loader.aload()
    # print(f"Loaded {len(documents)} from the database. 5 Examples:")
    # for doc in documents[:5]:
    #     print(doc)


# Run the async function
asyncio.run(load_documents())