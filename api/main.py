from fastapi import FastAPI, HTTPException
from datetime import datetime

from api.models.patient_models import PatientIn
from api.db.postgres import get_pg_conn
from api.db.mongo import get_mongo_db

app = FastAPI()

# --- PostgreSQL CRUD Endpoints ---
def get_or_create_id(cur, table, col, value):
    id_column_map = {
        "Sexes": "sex_id",
        "BloodPressures": "bp_id",
        "Cholesterols": "cholesterol_id"
    }
    id_col = id_column_map[table]
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {col} = %s", (value,))
    result = cur.fetchone()
    if result:
        return result[0]
    cur.execute(f"INSERT INTO {table} ({col}) VALUES (%s) RETURNING {id_col}", (value,))
    return cur.fetchone()[0]

@app.post("/patients/", status_code=201)
def create_patient_pg(data: PatientIn):
    with get_pg_conn() as conn:
        cur = conn.cursor()
        sex_id = get_or_create_id(cur, "Sexes", "sex_name", data.sex)
        bp_id = get_or_create_id(cur, "BloodPressures", "bp_level", data.bp)
        cholesterol_id = get_or_create_id(cur, "Cholesterols", "cholesterol_level", data.cholesterol)
        cur.execute("""
            INSERT INTO Patients (sex_id, bp_id, cholesterol_id, age, na_to_k)
            VALUES (%s, %s, %s, %s, %s) RETURNING patient_id
        """, (sex_id, bp_id, cholesterol_id, data.age, data.na_to_k))
        patient_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO DrugAssignments (patient_id, drug_type, assigned_at)
            VALUES (%s, %s, %s) RETURNING assignment_id
        """, (patient_id, data.drug, datetime.now()))
        assignment_id = cur.fetchone()[0]
        conn.commit()
        return {"patient_id": patient_id, "assignment_id": assignment_id}

@app.get("/patients/{patient_id}")
def read_patient_pg(patient_id: int):
    with get_pg_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.patient_id, p.age, s.sex_name, bp.bp_level, c.cholesterol_level, p.na_to_k, da.drug_type
            FROM Patients p
            JOIN Sexes s ON p.sex_id = s.sex_id
            JOIN BloodPressures bp ON p.bp_id = bp.bp_id
            JOIN Cholesterols c ON p.cholesterol_id = c.cholesterol_id
            LEFT JOIN DrugAssignments da ON da.patient_id = p.patient_id
            WHERE p.patient_id = %s
        """, (patient_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")
        return dict(zip(["patient_id", "age", "sex", "bp", "cholesterol", "na_to_k", "drug"], row))

@app.put("/patients/{patient_id}")
def update_patient_pg(patient_id: int, data: PatientIn):
    with get_pg_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT patient_id FROM Patients WHERE patient_id = %s", (patient_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Patient not found")
        sex_id = get_or_create_id(cur, "Sexes", "sex_name", data.sex)
        bp_id = get_or_create_id(cur, "BloodPressures", "bp_level", data.bp)
        cholesterol_id = get_or_create_id(cur, "Cholesterols", "cholesterol_level", data.cholesterol)
        cur.execute("""
            UPDATE Patients SET sex_id=%s, bp_id=%s, cholesterol_id=%s, age=%s, na_to_k=%s
            WHERE patient_id=%s
        """, (sex_id, bp_id, cholesterol_id, data.age, data.na_to_k, patient_id))
        cur.execute("""
            UPDATE DrugAssignments SET drug_type=%s, assigned_at=%s
            WHERE patient_id=%s
        """, (data.drug, datetime.now(), patient_id))
        conn.commit()
        return {"detail": "Patient updated"}

@app.delete("/patients/{patient_id}")
def delete_patient_pg(patient_id: int):
    with get_pg_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT patient_id FROM Patients WHERE patient_id = %s", (patient_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Patient not found")
        cur.execute("DELETE FROM DrugAssignments WHERE patient_id = %s", (patient_id,))
        cur.execute("DELETE FROM Patients WHERE patient_id = %s", (patient_id,))
        conn.commit()
        return {"detail": "Patient deleted"}

# --- MongoDB CRUD Endpoints ---
def get_or_create_id_mongo(collection, id_field, value_field, value):
    doc = collection.find_one({value_field: value})
    if doc:
        return doc[id_field]
    new_id = collection.count_documents({}) + 1
    collection.insert_one({id_field: new_id, value_field: value})
    return new_id

@app.post("/mongo/patients/", status_code=201)
def create_patient_mongo(data: PatientIn):
    db = get_mongo_db()
    sex_id = get_or_create_id_mongo(db.Sexes, "sex_id", "sex_name", data.sex)
    bp_id = get_or_create_id_mongo(db.BloodPressures, "bp_id", "bp_level", data.bp)
    cholesterol_id = get_or_create_id_mongo(db.Cholesterols, "cholesterol_id", "cholesterol_level", data.cholesterol)
    patient_id = db.Patients.count_documents({}) + 1
    db.Patients.insert_one({
        "patient_id": patient_id,
        "sex_id": sex_id,
        "bp_id": bp_id,
        "cholesterol_id": cholesterol_id,
        "age": data.age,
        "na_to_k": data.na_to_k
    })
    assignment_id = db.DrugAssignments.count_documents({}) + 1
    db.DrugAssignments.insert_one({
        "assignment_id": assignment_id,
        "patient_id": patient_id,
        "drug_type": data.drug,
        "assigned_at": datetime.utcnow()
    })
    return {"patient_id": patient_id, "assignment_id": assignment_id}

@app.get("/mongo/patients/{patient_id}")
def read_patient_mongo(patient_id: int):
    db = get_mongo_db()
    patient = db.Patients.find_one({"patient_id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    drug = db.DrugAssignments.find_one({"patient_id": patient_id})
    sex = db.Sexes.find_one({"sex_id": patient["sex_id"]})
    bp = db.BloodPressures.find_one({"bp_id": patient["bp_id"]})
    cholesterol = db.Cholesterols.find_one({"cholesterol_id": patient["cholesterol_id"]})
    return {
        "patient_id": patient["patient_id"],
        "age": patient["age"],
        "sex": sex["sex_name"] if sex else None,
        "bp": bp["bp_level"] if bp else None,
        "cholesterol": cholesterol["cholesterol_level"] if cholesterol else None,
        "na_to_k": patient["na_to_k"],
        "drug": drug["drug_type"] if drug else None
    }

@app.put("/mongo/patients/{patient_id}")
def update_patient_mongo(patient_id: int, data: PatientIn):
    db = get_mongo_db()
    patient = db.Patients.find_one({"patient_id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    sex_id = get_or_create_id_mongo(db.Sexes, "sex_id", "sex_name", data.sex)
    bp_id = get_or_create_id_mongo(db.BloodPressures, "bp_id", "bp_level", data.bp)
    cholesterol_id = get_or_create_id_mongo(db.Cholesterols, "cholesterol_id", "cholesterol_level", data.cholesterol)
    db.Patients.update_one(
        {"patient_id": patient_id},
        {"$set": {
            "sex_id": sex_id,
            "bp_id": bp_id,
            "cholesterol_id": cholesterol_id,
            "age": data.age,
            "na_to_k": data.na_to_k
        }}
    )
    db.DrugAssignments.update_one(
        {"patient_id": patient_id},
        {"$set": {
            "drug_type": data.drug,
            "assigned_at": datetime.utcnow()
        }}
    )
    return {"detail": "Patient updated"}

@app.delete("/mongo/patients/{patient_id}")
def delete_patient_mongo(patient_id: int):
    db = get_mongo_db()
    patient = db.Patients.find_one({"patient_id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.DrugAssignments.delete_many({"patient_id": patient_id})
    db.Patients.delete_one({"patient_id": patient_id})
    return {"detail": "Patient deleted"}