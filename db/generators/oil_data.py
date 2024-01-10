import csv
from typing import List
from faker import Faker
import random


class OilDataGenerator:
    def __init__(self):
        self.fake = Faker()

    def generate_csv(self, file_name: str, rows: int = 100) -> None:
        with open(file_name, "w", newline="") as csvfile:
            fieldnames = [
                "Company",
                "Well_Name",
                "Oil_Production_bbl",
                "Gas_Production_mcf",
                "Region",
                "Status",
                "Owner",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for _ in range(rows):
                data = self.generate_row()
                writer.writerow(
                    {fieldnames[i]: data[i] for i in range(len(fieldnames))}
                )

    def generate_row(self) -> List:
        geological_terms = [
            "Creek",
            "Hill",
            "Field",
            "Ridge",
            "Valley",
            "Mountain",
            "Lake",
            "River",
            "Ocean",
            "Forest",
            "Desert",
            "Swamp",
            "Canyon",
            "Bay",
            "Spring",
            "Cliff",
            "Plateau",
            "Dune",
            "Volcano",
            "Glacier",
            "Cave",
            "Island",
            "Marsh",
            "Prairie",
            "Reef",
            "Jungle",
            "Gulf",
            "Peninsula",
            "Falls",
            "Peak",
            "Pond",
            "Lagoon",
            "Meadow",
            "Delta",
            "Geyser",
            "Oasis",
            "Savannah",
            "Fjord",
            "Grove",
            "Tundra",
            "Basin",
            "Reservoir",
            "Archipelago",
            "Coral",
            "Isthmus",
            "Butte",
            "Mesa",
            "Cirque",
            "Saddle",
            "Seamount",
            "Strait",
            "Thicket",
            "Trench",
            "Vale",
            "Wetland",
        ]
        location = self.fake.city()
        identifier = str(random.randint(100, 999))
        well_name = location + " " + random.choice(geological_terms) + " " + identifier

        company = self.fake.company()
        oil_production = round(random.uniform(50, 500), 2)
        gas_production = round(random.uniform(100, 1000), 2)
        region = self.fake.state()
        status = random.choice(["Active", "Inactive"])
        owner = self.fake.name()
        return [
            company,
            well_name,
            oil_production,
            gas_production,
            region,
            status,
            owner,
        ]
