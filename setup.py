from db.generators.oil_data import OilDataGenerator
from db.seed import Seeder

# Seed your data of choice using a generator
oil_generator = OilDataGenerator()
seeder = Seeder(oil_generator)

file_name = "oil_data.csv"
table_name = "oil_data"

seeder.seed(file_name, table_name, rows=100)
