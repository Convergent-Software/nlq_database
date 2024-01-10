from typing import Optional
from pandas import DataFrame
from sqlalchemy import create_engine
from openai_query import OpenAIQuery
from pygwalker.api.streamlit import StreamlitRenderer, init_streamlit_comm
import os
import pandas as pd
import streamlit as st
import psycopg
import json


class UI:
    def __init__(self) -> None:
        self.initialize_session_state()

    def setup_pygwalker(self) -> None:
        init_streamlit_comm()

        @st.cache_resource
        def get_pyg_renderer() -> "StreamlitRenderer":
            connection_string = (
                f"postgresql+psycopg://"
                f"{os.getenv('DB_USER')}:"
                f"{os.getenv('DB_PASSWORD')}@"
                f"{os.getenv('DB_HOST')}:"
                f"{os.getenv('DB_PORT')}/"
                f"{os.getenv('DB_NAME')}"
            )
            engine = create_engine(connection_string)
            query = "SELECT * FROM oil_data"
            df = pd.read_sql_query(query, engine)
            return StreamlitRenderer(df, spec="./gw_config.json", debug=False)

        renderer = get_pyg_renderer()
        renderer.render_explore()

    def initialize_session_state(self) -> None:
        st.session_state.setdefault("tabs", ["Database Connection"])
        st.session_state.setdefault("active_tab", "Database Connection")

    def add_new_tab(self, new_tab_name):
        if new_tab_name and new_tab_name not in st.session_state["tabs"]:
            st.session_state["tabs"].append(new_tab_name)
            self.initialize_query_log(self.create_key("query_log", new_tab_name))

    def delete_all_tabs(self):
        st.session_state["tabs"] = ["Database Connection"]
        st.session_state["active_tab"] = "Database Connection"

    @staticmethod
    def create_key(prefix: str, tab_name: str) -> str:
        return f"{prefix}_{tab_name}"

    def handle_sidebar(self) -> None:
        with st.sidebar:
            pages = ["Database", "Schema", "Conversations", "Visualizations"]
            page = st.radio("Go to", pages)

            st.session_state["current_page"] = page

            if page == "Database":
                host = st.text_input("Host")
                port = st.text_input("Port")
                user = st.text_input("User")
                password = st.text_input("Password", type="password")
                dbname = st.text_input("Database")

                if st.button("Connect", type="primary"):
                    connection = self.connect_to_database(
                        host, port, user, password, dbname
                    )
                    if connection:
                        self.handle_successful_connection(connection)

                if st.button("Close Database"):
                    self.handle_close_database_button()

            elif page == "Schema":
                if "schema" in st.session_state:
                    schema = st.session_state["schema"]
                    for table_name, columns in schema.items():
                        st.markdown(f"<h3>📋{table_name}</h3>", unsafe_allow_html=True)
                        for column_name, data_type in columns.items():
                            st.markdown(f"🔹 {column_name} ({data_type})")
                else:
                    st.info("No schema available. Please connect to a database first.")

            elif page == "Conversations":
                new_tab_name = st.text_input("Enter name for new chat:")
                if st.button("Add", type="primary"):
                    self.add_new_tab(new_tab_name)

                if st.button("Clear chats"):
                    self.delete_all_tabs()

                for tab in st.session_state["tabs"]:
                    if tab != "Database Connection":
                        if st.button(tab):
                            st.session_state["active_tab"] = tab

            elif page == "Visualizations":
                pass

    def connect_to_database(
        self, host: str, port: str, user: str, password: str, dbname: str
    ):
        try:
            conn = psycopg.connect(
                host=host, port=port, user=user, password=password, dbname=dbname
            )
            return conn
        except psycopg.Error as e:
            st.error(f"Connection failed: {e}")
            return None

    def handle_database_connection_tab(self) -> None:
        if st.session_state["active_tab"] == "Database Connection":
            st.title("Database Connection")
            if "connection" in st.session_state:
                st.success("Connected to the database!")
                self.retrieve_and_store_schema(st.session_state["cursor"])
            else:
                st.error("Not connected to any database.")

    def handle_successful_connection(self, connection):
        cursor = connection.cursor()
        # Store connection and cursor in session state
        st.session_state["connection"] = connection
        st.session_state["cursor"] = cursor
        # Retrieve and store schema
        self.retrieve_and_store_schema(cursor)

    def retrieve_and_store_schema(self, cursor):
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

    def execute_sql_query(self, cursor, query: str) -> Optional[DataFrame]:
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=column_names)
            return df
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return None

    def initialize_query_log(self, tab_key: str) -> None:
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

    def handle_query_tab(self) -> None:
        if "cursor" not in st.session_state:
            st.session_state["cursor"] = None

        if st.session_state["active_tab"] != "Database Connection":
            selected_tab = st.session_state["active_tab"]
            st.title(selected_tab)

            self.initialize_query_log(selected_tab)
            self.handle_query_generation(selected_tab)
            self.display_generated_query(selected_tab)
            self.display_dataframe(selected_tab)

    def handle_query_generation(self, selected_tab):
        user_input_key = self.create_key("user_input", selected_tab)
        current_user_input = st.session_state.get(user_input_key, "")
        user_query = st.text_area(
            f"Enter your natural language query",
            value=current_user_input,
        )
        st.session_state[user_input_key] = user_query  # Store the current input

        if st.button("Generate SQL Query", key=f"button_{selected_tab}"):
            self.generate_sql_query(selected_tab, user_query)

    def generate_sql_query(self, selected_tab, user_query):
        tab_key = self.create_key("query_log", selected_tab)
        st.session_state[tab_key].append({"role": "user", "content": user_query})

        query = OpenAIQuery(api_key=os.getenv("OPENAI_API_KEY"))
        client = query.client
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=st.session_state[tab_key]
        )

        st.session_state[tab_key].append(
            {
                "role": "assistant",
                "content": response.choices[0].message.content.strip(),
            }
        )

        model_query = st.session_state[tab_key][-1]["content"]
        generated_query_key = self.create_key("generated_query", selected_tab)
        st.session_state[generated_query_key] = model_query

        df = self.execute_sql_query(
            cursor=st.session_state["cursor"],
            query=model_query,
        )
        if df is not None:
            dataframe_key = self.create_key("dataframe", selected_tab)
            st.session_state[dataframe_key] = df

    def display_generated_query(self, selected_tab):
        generated_query_key = self.create_key("generated_query", selected_tab)
        query_display_key = self.create_key("query_display", selected_tab)
        if generated_query_key in st.session_state:
            st.text_area(
                "Generated SQL Query:",
                value=st.session_state[generated_query_key],
                height=200,
                key=query_display_key,
            )

    def display_dataframe(self, selected_tab):
        dataframe_key = self.create_key("dataframe", selected_tab)
        if dataframe_key in st.session_state:
            st.dataframe(st.session_state[dataframe_key])

    def handle_close_database_button(self) -> None:
        if "cursor" in st.session_state and "connection" in st.session_state:
            st.session_state["cursor"].close()
            st.session_state["cursor"] = None
            st.session_state["active_tab"] = "Database Connection"
