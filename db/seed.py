import os
from typing import Any
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


class Seeder:
    def __init__(self, generator: Any):
        self.generator = generator
        self.params = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "dbname": os.getenv("DB_NAME"),
        }
        self.engine = create_engine(
            f"postgresql+psycopg://{self.params['user']}:{self.params['password']}@{self.params['host']}:{self.params['port']}/{self.params['dbname']}"
        )

    def create_table(self, table_name: str, file_name: str) -> None:
        df = pd.read_csv(file_name)
        columns = ", ".join([f"{col} TEXT" for col in df.columns])

        with self.engine.connect() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            connection.execute(text(f"CREATE TABLE {table_name} ({columns})"))

    def upload_csv_to_postgres(self, file_name: str, table_name: str) -> None:
        df = pd.read_csv(file_name)
        df.to_sql(table_name, self.engine, if_exists="append", index=False)

    def drop_table(self, table_name: str) -> None:
        with self.engine.connect() as connection:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

    def seed(self, file_name: str, table_name: str, rows: int = 100) -> None:
        try:
            self.generator.generate_csv(file_name, rows)
            self.create_table(table_name, file_name)
            self.upload_csv_to_postgres(file_name, table_name)
        except Exception as e:
            print(f"An error occurred: {e}")
            self.drop_table(table_name)
            raise e
