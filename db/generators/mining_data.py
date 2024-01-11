import csv
from typing import List
from faker import Faker
import random


class MiningDataGenerator:
    def __init__(self):
        self.fake = Faker()

    def generate_csv(self, file_name: str, rows: int = 100) -> None:
        with open(file_name, "w", newline="") as csvfile:
            fieldnames = [
                "company",
                "mine_name",
                "gold_production_oz",
                "silver_production_oz",
                "region",
                "status",
                "owner",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for _ in range(rows):
                data = self.generate_row()
                writer.writerow(
                    {fieldnames[i]: data[i] for i in range(len(fieldnames))}
                )

    def generate_row(self) -> List:
        company = self.fake.company()
        mine_name = self.fake.word() + " " + self.fake.word()
        gold_production = round(random.uniform(10, 100), 2)
        silver_production = round(random.uniform(50, 500), 2)
        region = self.fake.state()
        status = random.choice(["Active", "Inactive"])
        owner = self.fake.name()
        return [
            company,
            mine_name,
            gold_production,
            silver_production,
            region,
            status,
            owner,
        ]
