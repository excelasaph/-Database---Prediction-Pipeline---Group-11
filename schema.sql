CREATE TABLE Sexes (
    sex_id SERIAL PRIMARY KEY,
    sex_name CHAR(1) NOT NULL CHECK (sex_name IN ('M', 'F'))
);

CREATE TABLE BloodPressures (
    bp_id SERIAL PRIMARY KEY,
    bp_level VARCHAR(10) NOT NULL CHECK (bp_level IN ('HIGH', 'NORMAL', 'LOW'))
);

CREATE TABLE Cholesterols (
    cholesterol_id SERIAL PRIMARY KEY,
    cholesterol_level VARCHAR(10) NOT NULL CHECK (cholesterol_level IN ('HIGH', 'NORMAL'))
);

CREATE TABLE Patients (
    patient_id SERIAL PRIMARY KEY,
    sex_id INTEGER REFERENCES Sexes(sex_id),
    bp_id INTEGER REFERENCES BloodPressures(bp_id),
    cholesterol_id INTEGER REFERENCES Cholesterols(cholesterol_id),
    age INTEGER NOT NULL CHECK (age >= 15 AND age <= 74),
    na_to_k FLOAT NOT NULL CHECK (na_to_k >= 6.0 AND na_to_k <= 40.0)
);

CREATE TABLE BloodPressures (
    bp_id SERIAL PRIMARY KEY,
    bp_level VARCHAR(10) NOT NULL CHECK (bp_level IN ('HIGH', 'NORMAL', 'LOW'))
);

-- Drop the trigger and function with CASCADE
DROP TRIGGER IF EXISTS patient_insert_trigger ON Patients;
DROP FUNCTION IF EXISTS log_new_patient_trigger() CASCADE;
DROP PROCEDURE IF EXISTS log_new_patient;

-- Recreate the procedure (logging only, no drug assignment)
CREATE OR REPLACE PROCEDURE log_new_patient(patient_id INTEGER)
LANGUAGE plpgsql
AS $$
BEGIN
    NULL;
END;
$$;

-- Recreate the trigger function using CALL
CREATE OR REPLACE FUNCTION log_new_patient_trigger()
RETURNS TRIGGER AS $$
BEGIN
    CALL log_new_patient(NEW.patient_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
CREATE TRIGGER patient_insert_trigger
AFTER INSERT ON Patients
FOR EACH ROW
EXECUTE FUNCTION log_new_patient_trigger();
