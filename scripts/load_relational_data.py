import psycopg2
import pandas as pd

# Connect to NeonDB
conn = psycopg2.connect("postgresql://neondb_owner:npg_YarpRPv27KLc@ep-cool-bonus-ab2dfy4h-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
cur = conn.cursor()

# Load CSV
df = pd.read_csv('c:/Users/Excel/Desktop/Github Projects/-Database---Prediction-Pipeline---Group-11/data/drug200.csv')  

# Insert unique Sex values
for sex in df['Sex'].dropna().unique():
    cur.execute("INSERT INTO Sexes (sex_name) VALUES (%s) ON CONFLICT DO NOTHING", (sex,))

# Insert unique BP values
for bp in df['BP'].dropna().unique():
    cur.execute("INSERT INTO BloodPressures (bp_level) VALUES (%s) ON CONFLICT DO NOTHING", (bp,))

# Insert unique Cholesterol values
for chol in df['Cholesterol'].dropna().unique():
    cur.execute("INSERT INTO Cholesterols (cholesterol_level) VALUES (%s) ON CONFLICT DO NOTHING", (chol,))

conn.commit()
cur.close()
conn.close()