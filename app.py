import os
import psycopg
import json
import pandas as pd
import streamlit as st

from pandas import DataFrame
from typing import Optional
from dotenv import load_dotenv
from openai_query import OpenAIQuery
from utils import format_as_dataframe

load_dotenv()


def execute_sql_query(cursor, query: str) -> Optional[DataFrame]:
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=column_names)
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None


def connect_to_database(host: str, port: str, user: str, password: str, dbname: str):
    try:
        conn = psycopg.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        return conn
    except psycopg.Error as e:
        st.error(f"Connection failed: {e}")
        return None


def create_key(prefix: str, tab_name: str) -> str:
    return f"{prefix}_{tab_name}"


def initialize_session_state() -> None:
    if "tabs" not in st.session_state:
        st.session_state["tabs"] = ["Database Connection"]
    if "active_tab" not in st.session_state:
        st.session_state["active_tab"] = "Database Connection"


def add_tab(tab_name: str) -> None:
    if tab_name and tab_name not in st.session_state["tabs"]:
        st.session_state["tabs"].append(tab_name)


def handle_sidebar() -> None:
    if "tabs" not in st.session_state:
        st.session_state["tabs"] = []
    with st.sidebar:
        new_tab_name = st.text_input("Enter name for new tab:")

        if st.markdown(
            '<a href="#" class="red-button">Add Tab</a>', unsafe_allow_html=True
        ):
            add_tab(new_tab_name)

        st.sidebar.title("Navigation")

        # Create a button for each tab
        for tab in st.session_state["tabs"]:
            if st.button(tab):
                st.session_state["active_tab"] = tab


def handle_database_connection_tab() -> None:
    if st.session_state["active_tab"] == "Database Connection":
        st.title("Database Connection")
        host = st.text_input("Host")
        port = st.text_input("Port")
        user = st.text_input("User")
        password = st.text_input("Password", type="password")
        dbname = st.text_input("Database")

        if st.button("Connect"):
            connection = connect_to_database(host, port, user, password, dbname)
            if connection:
                st.success("Connected to the database!")
                cursor = connection.cursor()
                # Store connection and cursor in session state
                st.session_state["connection"] = connection
                st.session_state["cursor"] = cursor
                # Retrieve and store schema
                cursor.execute(
                    """
                SELECT 
                    table_name, 
                    column_name, 
                    data_type 
                FROM 
                    information_schema.columns 
                WHERE 
                    table_schema = 'public';
                """
                )
                schema_data = cursor.fetchall()
                schema = {}
                for table, column, datatype in schema_data:
                    if table not in schema:
                        schema[table] = {}
                    schema[table][column] = datatype
                st.session_state["schema"] = schema
                formatted_schema = json.dumps(schema, indent=4)
                st.session_state["formatted_schema"] = formatted_schema
                st.json(formatted_schema)


def handle_query_tab() -> None:
    if "cursor" not in st.session_state:
        st.session_state["cursor"] = None

    if st.session_state["active_tab"] != "Database Connection":
        selected_tab = st.session_state["active_tab"]
        st.title(f"Natural Language to SQL Query - {selected_tab}")

        query = OpenAIQuery(api_key=os.getenv("OPENAI_API_KEY"))
        client = query.client

        model_id = "gpt-3.5-turbo"

        tab_key = create_key("query_log", selected_tab)
        if tab_key not in st.session_state:
            st.session_state[tab_key] = [
                {
                    "role": "system",
                    "content": (
                        f"You are a professional postgresql query writer. The user will provide you "
                        f"with a natural language query and your job is to convert that to SQL based "
                        f"on the schema of the users database: {st.session_state.get('formatted_schema', '{}')}. "
                        f"Think step-by-step through the process to make sure the query makes sense "
                        f"and includes columns that actually exist in each table. Only output the SQL query "
                        f"and make sure to add ';' at the end so the query can be run. Your output will be used "
                        f"in a function to query a database so it is important not to return another other text "
                        f"if your response. Do not include any explanation."
                    ),
                }
            ]

        user_input_key = create_key("user_input", selected_tab)
        generated_query_key = create_key("generated_query", selected_tab)
        query_display_key = create_key("query_display", selected_tab)
        dataframe_key = create_key("dataframe", selected_tab)

        current_user_input = st.session_state.get(user_input_key, "")
        user_query = st.text_area(
            f"Enter your natural language query for {selected_tab}:",
            value=current_user_input,
        )
        st.session_state[user_input_key] = user_query  # Store the current input

        if st.button("Generate SQL Query", key=f"button_{selected_tab}"):
            st.session_state[tab_key].append({"role": "user", "content": user_query})
            response = client.chat.completions.create(
                model=model_id, messages=st.session_state[tab_key]
            )
            st.session_state[tab_key].append(
                {
                    "role": "assistant",
                    "content": response.choices[0].message.content.strip(),
                }
            )
            model_query = st.session_state[tab_key][-1]["content"]
            st.session_state[generated_query_key] = model_query

            df = execute_sql_query(
                cursor=st.session_state["cursor"],
                query=model_query,
                # formatter=format_as_dataframe,
                # error_handler=st.error,
            )
            if df is not None:
                st.session_state[dataframe_key] = df

        # Display the stored generated query and DataFrame if they exist
        if generated_query_key in st.session_state:
            st.text_area(
                "Generated SQL Query:",
                value=st.session_state[generated_query_key],
                height=200,
                key=query_display_key,
            )

        # Display the DataFrame if it exists
        if dataframe_key in st.session_state:
            st.dataframe(st.session_state[dataframe_key])

        # Close the connection button
        if st.button("Close Database Connection", key=f"close_{selected_tab}"):
            if "cursor" in st.session_state and "connection" in st.session_state:
                st.session_state["cursor"].close()
                st.session_state["connection"].close()
                st.success("Database connection closed.")


def main():
    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )

    initialize_session_state()
    handle_sidebar()
    handle_database_connection_tab()
    handle_query_tab()


if __name__ == "__main__":
    main()
