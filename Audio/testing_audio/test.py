from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from openai import OpenAI
import os
from dotenv import load_dotenv

from contextlib import redirect_stdout, redirect_stderr
import io

### Make sure that the API key from the .env file is being loaded in
load_dotenv()
api_key = os.getenv('NEW_OPENAI_API_KEY')

# print(f"The value of the api_key is {api_key}")
# To avoid warning?
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

def answer_course_question_new(question: str):
    vn = MyVanna(config={'api_key': api_key, 'model': 'gpt-3.5-turbo'})
    vn.connect_to_postgres(host='34.60.28.103', dbname='tutorialDB', user='postgres', password='butlar', port='5432')
    
    ### To make sure that the training data is being inherited properly:
    training_data = vn.get_training_data()
    # print(f"The value of training_data is {training_data}")


    try:
        # Redirects all outputs into this standard output
        dummy_output = io.StringIO()
        # Redirects all errors into this standard error
        dummy_error = io.StringIO()


        with redirect_stderr(dummy_error), redirect_stdout(dummy_output):
            response = vn.ask(question=question, allow_llm_to_see_data=True, print_results=False)
        
        if "Couldn't" in dummy_output.getvalue():
            # Add someway for the user to add input to retrain the information to ask again
            print(f"The value of response is: {response}")
            raise ValueError(f"The question of \"{question}\" was asked incorrectly or the answer does not exist in the database. Please ask again.")
        
        if len(response) < 2:
            raise ValueError("Response tuple only contains SQL query (missing results DataFrame)")
        
        # Response[0] is just like the SQL information about the table. Includes what vanna is parsing through
        results_df = response[1]

        
        # Check if the DataFrame is empty
        if results_df.empty:
            # print(f"Here is the value of the response: {response}")
            raise RuntimeError("Results Dataframe is empty.")
        # print(f"The value of response is: {response}")
        
        return results_df
    
    ### Add training logic to here so that if Vanna got it wrong, can add documentation:
    # vn.train(documentation="")
    except ValueError as e:
        return f"Error occured: {e}"
    except RuntimeError as e:
        return f"Error during Runtime: {e}"
    
    # Don't know if this actually works or not lol, made by chat
    except IndexError as e:
        return f"Error: Response tuple is missing expected elements - {str(e)}"
    except Exception as e:
        return f"Error processing question: {str(e)}"

def interpret_vanna_msg(my_question):

    vanna_ans_tables = answer_course_question_new(my_question)
    if "Error" in vanna_ans_tables:
        return vanna_ans_tables

    # Not sure why I had to do this change but I did
    client = OpenAI(api_key=api_key)
    # client.api_key = api_key

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "developer", "content": "You are a helpful assistant in interpreting data tables into complete sentences and an intelligible response."},
        {"role": "user", "content": f"Answer the question of: {my_question}, given this data table of{vanna_ans_tables}"}
        ]
    )
    # print(f"The answer is {completion.choices[0].message.content}")
    return completion.choices[0].message.content

# response = interpret_vanna_msg("What courses does Ajay Joshi teach? What are the course titles and what time do these courses meet?")
# print(f"The value of response is {response}")