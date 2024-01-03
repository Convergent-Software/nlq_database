import psycopg2
import json
import pandas as pd
import getpass
from openai import OpenAI
import streamlit as st

# Initializing tabs
tab1, tab2, tab3 = st.tabs(['Database Connection', 'Natural Language Querying', 'Data Visualization'])

# Page 1: Connection and Schema Collection
with tab1:
    def connect_to_database(host, port, user, password, database):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            return conn
        except psycopg2.Error as e:
            st.error(f"Connection failed: {e}")
            return None

    st.title("Database Connection")
    host = st.text_input("Host")
    port = st.text_input("Port")
    user = st.text_input("User")
    password = st.text_input("Password", type="password")
    database = st.text_input("Database")

    if st.button("Connect"):
        connection = connect_to_database(host, port, user, password, database)
        if connection:
            st.success("Connected to the database!")
            cursor = connection.cursor()
            # Store connection and cursor in session state
            st.session_state['connection'] = connection
            st.session_state['cursor'] = cursor
            # Retrieve and store schema
            cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type 
            FROM 
                information_schema.columns 
            WHERE 
                table_schema = 'public';
            """)
            schema_data = cursor.fetchall()
            schema = {}
            for table, column, datatype in schema_data:
                if table not in schema:
                    schema[table] = {}
                schema[table][column] = datatype
            st.session_state['schema'] = schema
            formatted_schema = json.dumps(schema, indent=4)
            st.session_state['formatted_schema'] = formatted_schema
            st.json(formatted_schema)

# Page 2: Natural Language Querying
with tab2:
    api_key = st.text_input("Enter your OpenAI API key:", type="password")
    if api_key:
        st.session_state['api_key'] = api_key
        client = OpenAI(api_key=st.session_state['api_key'])

    model_id = 'gpt-3.5-turbo'

    # Define the function for OpenAI conversation
    def nlq_conversation(query_log):
        response = client.chat.completions.create(
            model=model_id,
            messages=query_log
        )
        query_log.append({'role': response.choices[0].message.role, 
                        'content': response.choices[0].message.content.strip()})
        return query_log

    # Streamlit interface for user query
    st.title("Natural Language to SQL Query")
    user_query = st.text_area("Enter your natural language query:")
    if st.button("Generate SQL Query"):
        if 'query_log' not in st.session_state:
            st.session_state['query_log'] = [{'role': 'system', 
                                            'content': f'You are a professional postgresql query writer. The user will provide you with a natural language query and your job is to conver that to SQL based on the schema of the users database: {st.session_state.get("formatted_schema", "{}")}. Think step-by-step through the process to make sure the query makes sense and includes colimns that actually exist in each table. Only output the SQL query and make sure to add ";" at the end so the query can be run. Your output will be used in a function to query a database so it is important not to return another other text if your response. Do not include any explanation.'}]

        st.session_state['query_log'].append({'role': 'user', 'content': user_query})
        st.session_state['query_log'] = nlq_conversation(st.session_state['query_log'])
        model_query = st.session_state['query_log'][-1]['content']

        st.text_area("Generated SQL Query:", value=model_query, height=200)

        # Execute the SQL query
        try:
            cursor = st.session_state['cursor']
            cursor.execute(model_query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error executing query: {e}")

    # (Optional) Close the connection button
    if st.button("Close Database Connection"):
        if 'cursor' in st.session_state and 'connection' in st.session_state:
            st.session_state['cursor'].close()
            st.session_state['connection'].close()
            st.success("Database connection closed.")