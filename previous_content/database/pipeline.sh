# Integrating LLM / Cloud
# Separated into tasks and running respective shell commands as necessary
# Andrew Sasamori, Suhani Mitra
# EC 463 Senior Design

# Required dependencies:
# %pip install --upgrade --quiet langchain-google-cloud-sql-pg langchain-google-vertexai langchain


# task 1
project_id="sanguine-orb-441020-p6"
instance_name="langchain-quickstart-instance"
databse_name="ec463-temp-database"
python init.py
# end task 1

gcloud config set project $project_id

# add permissions to the user
current_user="andrewsasamori@gmail.com"

gcloud auth list --filter=status:ACTIVE --format="value(account)"
gcloud projects add-iam-policy-binding $project_id \
  --member=user:$current_user \
  --role="roles/cloudsql.client"

# echo "We have added the necessary permissions to the user"

# Enable GCP services
gcloud services enable sqladmin.googleapis.com aiplatform.googleapis.com


# Integrating our various use cases



# task 2 - use case 1
python case1.py
# end task 2



# task 3 - use case 2
python case2.py
# end task 3


project_id="sanguine-orb-441020-p6"
instance_name="langchain-quickstart-instance"
database_name="ec463-temp-database"
gcloud sql import sql $instance_name gs://cloud-samples-data/langchain/cloud-sql/postgres/netflix_titles_vector_table.sql --database=$database_name --quiet


# task 4 - use case 3
python case3.py
# end task 4


# task 5 - conversation

# modify this to use our own conversation inputs
python conversation.py

# end task 5