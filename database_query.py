import psycopg
import json
import os

from openai_query import OpenAIQuery
from utils import format_as_dict
from typing import Callable, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class DatabaseQuery:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.schema = None
        self.openai_query = OpenAIQuery(os.getenv("OPENAI_API_KEY"))
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.dbname = os.getenv("DB_NAME")

    def connect_to_database(self) -> None:
        try:
            self.conn = psycopg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname,
            )
            self.cursor = self.conn.cursor()
        except psycopg.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def fetch_schema(self) -> None:
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

        self.cursor.execute(query)
        schema_data = self.cursor.fetchall()
        self.schema = {}

        for table, column, datatype in schema_data:
            if table not in self.schema:
                self.schema[table] = {}
            self.schema[table][column] = datatype

    def execute_query_and_fetch_results(
        self,
        query: str,
        formatter: Optional[Callable[[List[List[Any]], List[str]], Any]] = None,
        error_handler: Callable[[str], None] = print,
    ) -> Optional[Any]:
        try:
            self.cursor.execute(query)
            column_names = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            if formatter is not None:
                return formatter(rows, column_names)
            else:
                return rows
        except psycopg.Error as e:
            error_message = f"An error occurred while executing the SQL query: {e}"
            error_handler(error_message)
            return None

    def run(self) -> None:
        try:
            self.connect_to_database()
            self.fetch_schema()
            self.openai_query.setup_openai_client()
            self.interact()
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()

    def interact(self) -> None:
        formatted_schema = json.dumps(self.schema, indent=4)
        system_message = self.openai_query.create_system_message(formatted_schema)
        self.openai_query.query.append(system_message)
        self.openai_query.query = self.openai_query.nlq_conversation(
            self.openai_query.query
        )

        while True:
            model_query = self.openai_query.handle_user_input()
            results = self.execute_query_and_fetch_results(
                model_query, formatter=format_as_dict
            )
            if results is not None:
                print(results)
                break


app = DatabaseQuery()
app.run()
