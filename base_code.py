import psycopg2
import json
import getpass
from openai import OpenAI

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password=getpass.getpass("Enter the database password: "),
    database='postgres'
)

cursor = conn.cursor()

# Query to get table and column information
query = """
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM 
    information_schema.columns 
WHERE 
    table_schema = 'public';
"""

cursor.execute(query)

# Fetching the results
schema_data = cursor.fetchall()

# Convert schema data to a JSON-like structure
schema = {}
for table, column, datatype in schema_data:
    if table not in schema:
        schema[table] = {}
    schema[table][column] = datatype

# The schema is now stored in the 'schema' variable as a JSON-like object
formatted_schema = json.dumps(schema, indent=4)

API_KEY = getpass.getpass("Enter your openai API key: ")

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key= API_KEY,
)

model_id = 'gpt-3.5-turbo'

def nlq_conversation(query_log):
    response = client.chat.completions.create(
        model = model_id,
        messages = query_log
    )
    query_log.append({'role': response.choices[0].message.role, 
                      'content': response.choices[0].message.content.strip()})
    return query_log

query =[]
query.append({'role': 'system', 
              'content': f'You are a professional postgresql query writer. The user will provide you with a natural language query and your job is to conver that to SQL based on the schema of the users database: {formatted_schema}. Think step-by-step through the process to make sure the query makes sense and includes colimns that actually exist in each table. Only output the SQL query and make sure to add ";" at the end so the query can be run. Your output will be used in a function to query a database so it is important not to return another other text if your response. Do not include any explanation.'})
query = nlq_conversation(query)

while True:
    prompt = input("Enter your query: ")
    query.append({'role': 'user', 'content': prompt})
    query = nlq_conversation(query)
    model_query = query[-1]['content']
    print(model_query)

    # Execute model_query
    cursor.execute(model_query)

    # Fetching column names from cursor.description
    column_names = [desc[0] for desc in cursor.description]

    # Fetching all rows from the query
    rows = cursor.fetchall()

    # Creating a list of dictionaries for each row
    results = []
    for row in rows:
        row_dict = dict(zip(column_names, row))
        results.append(row_dict)

    print(results)

# Close the connection
cursor.close()
conn.close()
    



