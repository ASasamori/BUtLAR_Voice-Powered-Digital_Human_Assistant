from langchain_google_cloud_sql_pg import PostgresChatMessageHistory

from case1 import pg_engine

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