import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://excel:LNS0e1g0eA8e7xMq@drug-cluster.cut2esi.mongodb.net/?retryWrites=true&w=majority&appName=drug-cluster")
db = client["drug-db"]

# Load CSV
df = pd.read_csv('c:/Users/Excel/Desktop/Github Projects/-Database---Prediction-Pipeline---Group-11/data/drug200.csv')

# Insert unique Sex values
for i, sex in enumerate(df['Sex'].dropna().unique(), start=1):
    db.Sexes.update_one(
        {"sex_name": sex},
        {"$setOnInsert": {"sex_id": i, "sex_name": sex}},
        upsert=True
    )

# Insert unique BP values with bp_id
for i, bp in enumerate(df['BP'].dropna().unique(), start=1):
    db.BloodPressures.update_one(
        {"bp_level": bp},
        {"$setOnInsert": {"bp_id": i, "bp_level": bp}},
        upsert=True
    )

# Insert unique Cholesterol values with cholesterol_id
for i, chol in enumerate(df['Cholesterol'].dropna().unique(), start=1):
    db.Cholesterols.update_one(
        {"cholesterol_level": chol},
        {"$setOnInsert": {"cholesterol_id": i, "cholesterol_level": chol}},
        upsert=True
    )

client.close()