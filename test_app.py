import psycopg2
import json
import pandas as pd
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

st.markdown("""
<style>
.red-button {
    background-color: darkred;
    color: white !important;
    padding: 8px 16px;
    border-radius: 4px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
}
.red-button:hover {
    background-color: red;
    color: white;
    text-decoration: none;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for tabs if not already done
if 'tabs' not in st.session_state:
    st.session_state['tabs'] = ['Database Connection']  # Default tab
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 'Database Connection'

# Sidebar for adding new tabs
with st.sidebar:
    new_tab_name = st.text_input("Enter name for new tab:")

    # Markdown styled as a button
    if st.markdown('<a href="#" class="red-button">Add Tab</a>', unsafe_allow_html=True):
        if new_tab_name and new_tab_name not in st.session_state['tabs']:
            st.session_state['tabs'].append(new_tab_name)

    st.sidebar.title("Navigation")

    # Create a button for each tab
    for tab in st.session_state['tabs']:
        if st.button(tab):
            st.session_state['active_tab'] = tab

if st.session_state['active_tab'] == 'Database Connection':
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

elif st.session_state['active_tab'] != 'Database Connection':
    selected_tab = st.session_state['active_tab']
    st.title(f"Natural Language to SQL Query - {selected_tab}")

    api_key = os.getenv('API_KEY')
    if api_key:
        client = OpenAI(api_key=api_key)

    model_id = 'gpt-3.5-turbo'

    tab_key = f"query_log_{selected_tab}"  # Unique key for each tab
    if tab_key not in st.session_state:
        st.session_state[tab_key] = [{'role': 'system', 
                                      'content': f'You are a professional postgresql query writer. The user will provide you with a natural language query and your job is to conver that to SQL based on the schema of the users database: {st.session_state.get("formatted_schema", "{}")}. Think step-by-step through the process to make sure the query makes sense and includes colimns that actually exist in each table. Only output the SQL query and make sure to add ";" at the end so the query can be run. Your output will be used in a function to query a database so it is important not to return another other text if your response. Do not include any explanation.'}]
    
    user_input_key = f"user_input_{selected_tab}" #Unique key for each user input
    generated_query_key = f"generated_query_{selected_tab}"
    query_display_key = f"query_display_{selected_tab}"
    dataframe_key = f"dataframe_{selected_tab}"

    current_user_input = st.session_state.get(user_input_key, '')
    user_query = st.text_area(f"Enter your natural language query for {selected_tab}:", value=current_user_input)
    st.session_state[user_input_key] = user_query  # Store the current input

    if st.button("Generate SQL Query", key=f"button_{selected_tab}"):
        st.session_state[tab_key].append({'role': 'user', 'content': user_query})
        response = client.chat.completions.create(
            model=model_id,
            messages=st.session_state[tab_key]
        )
        st.session_state[tab_key].append({'role': 'assistant', 
                                          'content': response.choices[0].message.content.strip()})
        model_query = st.session_state[tab_key][-1]['content']
        st.session_state[generated_query_key] = model_query

        # Execute the SQL query (assuming cursor is available)
        try:
            cursor = st.session_state['cursor']
            cursor.execute(model_query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
            st.session_state[dataframe_key] = df  # Store the DataFrame
        except Exception as e:
            st.error(f"Error executing query: {e}")

    # Display the stored generated query and DataFrame if they exist
    if generated_query_key in st.session_state:
        st.text_area("Generated SQL Query:", value=st.session_state[generated_query_key], height=200, key=query_display_key)

    # Display the DataFrame if it exists
    if dataframe_key in st.session_state:
        st.dataframe(st.session_state[dataframe_key])

    # Close the connection button
    if st.button("Close Database Connection", key=f"close_{selected_tab}"):
        if 'cursor' in st.session_state and 'connection' in st.session_state:
            st.session_state['cursor'].close()
            st.session_state['connection'].close()
            st.success("Database connection closed.")