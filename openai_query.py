from openai import OpenAI
from typing import List, Dict


class OpenAIQuery:
    def __init__(self, api_key: str, model_id: str = "gpt-3.5-turbo"):
        self._client = None
        self.model_id = model_id
        self.api_key = api_key
        self.query: List[Dict[str, str]] = []

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def create_system_message(self, formatted_schema: str) -> Dict[str, str]:
        return {
            "role": "system",
            "content": (
                f"You are a professional postgresql query writer. The user will provide you "
                f"with a natural language query and your job is to convert that to SQL based "
                f"on the schema of the users database: {formatted_schema}. Think step-by-step "
                f"through the process to make sure the query makes sense and includes columns "
                f"that actually exist in each table. Only output the SQL query and make sure "
                f"to add ';' at the end so the query can be run. Your output will be used in "
                f"a function to query a database so it is important not to return another "
                f"other text if your response. Do not include any explanation."
            ),
        }

    def handle_user_input(self) -> str:
        prompt = input("Enter your query: ")
        self.query.append({"role": "user", "content": prompt})
        self.query = self.nlq_conversation(self.query)
        model_query = self.query[-1]["content"]
        print(model_query)
        return model_query

    def nlq_conversation(self, query_log: List[Dict[str, str]]) -> List[Dict[str, str]]:
        response = self.client.chat.completions.create(
            model=self.model_id, messages=query_log
        )
        query_log.append(
            {
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content.strip(),
            }
        )
        return query_log
