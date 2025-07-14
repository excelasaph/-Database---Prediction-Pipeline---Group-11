from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime

from api.models.patient_models import PatientIn
from api.db.postgres import get_pg_conn
from api.db.mongo import get_mongo_db
from api.models.prediction_log_models import PredictionLogIn

import joblib
import os
import numpy as np
import pandas as pd
from typing import Optional

# For Keras model loading
try:
    from tensorflow.keras.models import load_model as keras_load_model
except ImportError:
    keras_load_model = None

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

# --- Latest Patient Endpoint (must be before /patients/{patient_id}) ---
@app.get("/patients/latest")
def get_latest_patient():
    patient = fetch_latest_patient_pg()
    if patient:
        return patient
    patient = fetch_latest_patient_mongo()
    if patient:
        return patient
    raise HTTPException(status_code=404, detail="No patients found in either database.")

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
    drug = db.DrugAssignments.find_one({"patient_id": patient["patient_id"]})
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

# Utility: Fetch latest patient from PostgreSQL, fallback to MongoDB

def fetch_latest_patient_pg():
    try:
        with get_pg_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.patient_id, p.age, s.sex_name, bp.bp_level, c.cholesterol_level, p.na_to_k, da.drug_type
                FROM Patients p
                JOIN Sexes s ON p.sex_id = s.sex_id
                JOIN BloodPressures bp ON p.bp_id = bp.bp_id
                JOIN Cholesterols c ON p.cholesterol_id = c.cholesterol_id
                LEFT JOIN DrugAssignments da ON da.patient_id = p.patient_id
                ORDER BY p.patient_id DESC LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                return None
            return dict(zip(["patient_id", "age", "sex", "bp", "cholesterol", "na_to_k", "drug"], row))
    except Exception:
        return None

def fetch_latest_patient_mongo():
    try:
        db = get_mongo_db()
        patient = db.Patients.find_one(sort=[("patient_id", -1)])
        if not patient:
            return None
        drug = db.DrugAssignments.find_one({"patient_id": patient["patient_id"]})
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
    except Exception:
        return None

# --- Prediction Endpoint ---

class PredictionRequest(BaseModel):
    model_type: str

@app.post("/predict")
def predict_latest_patient(data: PredictionRequest):
    model_type = data.model_type
    
    # Only allow neural network model
    if model_type != "nn":
        raise HTTPException(status_code=400, detail="Only 'nn' model type is supported. Please use 'nn'.")
    
    # Load preprocessor
    preproc_path = os.path.join(os.path.dirname(__file__), "..", "encoders", "preprocessor.pkl")
    preproc_path = os.path.abspath(preproc_path)
    if not os.path.exists(preproc_path):
        raise HTTPException(status_code=500, detail=f"Preprocessor file not found at: {preproc_path}")
    preprocessor = joblib.load(preproc_path)
    
    # Load neural network model
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "saved_models", "model_nn_optimized.keras")
    model_path = os.path.abspath(model_path)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=500, detail=f"Neural network model file not found at: {model_path}")
    
    if keras_load_model is None:
        raise HTTPException(status_code=500, detail="TensorFlow/Keras not installed.")
    model = keras_load_model(model_path)
    
    # Fetch latest patient
    patient = fetch_latest_patient_pg()
    db_used = "postgresql"
    if not patient:
        patient = fetch_latest_patient_mongo()
        db_used = "mongodb"
    if not patient:
        raise HTTPException(status_code=404, detail="No patients found in either database.")
    
    # Prepare data for prediction
    features = ["Age", "Sex", "BP", "Cholesterol", "Na_to_K"]
    X = pd.DataFrame([{
        "Age": patient["age"],
        "Sex": patient["sex"],
        "BP": patient["bp"],
        "Cholesterol": patient["cholesterol"],
        "Na_to_K": patient["na_to_k"]
    }])
    
    try:
        X_proc = preprocessor.transform(X)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")
    
    # Predict using neural network
    try:
        pred = model.predict(X_proc)
        pred_label = np.argmax(pred, axis=1)[0]
        
        # Map prediction index to drug name
        drug_mapping = {0: "DrugY", 1: "drugA", 2: "drugB", 3: "drugC", 4: "drugX"}
        pred_drug = drug_mapping.get(pred_label, f"Unknown_{pred_label}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
    return {
        "db_used": db_used,
        "model_type": model_type,
        "prediction": pred_drug,
        "actual": patient["drug"],
        "patient_features": {
            "age": patient["age"],
            "sex": patient["sex"],
            "bp": patient["bp"],
            "cholesterol": patient["cholesterol"],
            "na_to_k": patient["na_to_k"]
        }
    }
