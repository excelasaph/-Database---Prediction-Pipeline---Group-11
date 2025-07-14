# Drug Classification Prediction Pipeline

A machine learning pipeline for drug classification using both relational (PostgreSQL) and NoSQL (MongoDB) databases, with a FastAPI-based REST API and automated prediction capabilities.

## Project Overview

This project implements a complete drug classification system that predicts the appropriate drug type based on patient characteristics. The system features dual database support, comprehensive CRUD operations, and an automated prediction pipeline.

### Key Features

- **Dual Database Support**: PostgreSQL (relational) and MongoDB (NoSQL)
- **Machine Learning Pipeline**: Neural network-based drug classification
- **RESTful API**: FastAPI with comprehensive CRUD operations
- **Automated Prediction**: Script-based prediction pipeline
- **Data Validation**: Robust input validation and error handling
- **Database Fallback**: Automatic fallback between databases

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │   PostgreSQL    │    │    MongoDB      │
│   (CRUD + ML)   │◄──►│   (Relational)  │    │   (NoSQL)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Prediction     │
│  Script         │
└─────────────────┘
```

## Database Schema

### PostgreSQL Schema
- **Patients**: Core patient information with foreign keys
- **Sexes**: Patient gender lookup table
- **BloodPressures**: Blood pressure levels lookup
- **Cholesterols**: Cholesterol levels lookup
- **DrugAssignments**: Drug prescriptions with timestamps

### MongoDB Collections
- **Patients**: Patient documents with embedded references
- **Sexes**: Gender collection
- **BloodPressures**: Blood pressure collection
- **Cholesterols**: Cholesterol collection
- **DrugAssignments**: Drug assignment documents

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- MongoDB database
- TensorFlow (for neural network predictions)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd -Database---Prediction-Pipeline---Group-11
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up databases**
   - Configure PostgreSQL connection in `api/db/postgres.py`
   - Configure MongoDB connection in `api/db/mongo.py`
   - Run the schema.sql file in your PostgreSQL database

4. **Start the API server**
   ```bash
   python -m uvicorn api.main:app --reload
   ```

5. **Run the prediction script**
   ```bash
   python scripts/predict_latest_patient.py
   ```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Available Endpoints

#### Patient Management (PostgreSQL)
- `POST /patients/` - Create a new patient
- `GET /patients/{patient_id}` - Get patient by ID
- `PUT /patients/{patient_id}` - Update patient
- `DELETE /patients/{patient_id}` - Delete patient
- `GET /patients/latest` - Get the latest patient

#### Patient Management (MongoDB)
- `POST /mongo/patients/` - Create a new patient
- `GET /mongo/patients/{patient_id}` - Get patient by ID
- `PUT /mongo/patients/{patient_id}` - Update patient
- `DELETE /mongo/patients/{patient_id}` - Delete patient

#### Prediction
- `POST /predict` - Make a drug prediction for the latest patient

### Example API Usage

#### Create a Patient
```bash
curl -X POST "http://localhost:8000/patients/" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "sex": "M",
    "bp": "HIGH",
    "cholesterol": "HIGH",
    "na_to_k": 15.2,
    "drug": "DrugY"
  }'
```

#### Make a Prediction
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"model_type": "nn"}'
```

## Machine Learning Pipeline

### Model Training
The project includes a comprehensive Jupyter notebook (`models/models_training.ipynb`) that trains multiple models:

- **Logistic Regression**: Baseline classification model
- **Gradient Boosting**: Ensemble method for improved accuracy
- **Random Forest**: Tree-based ensemble model
- **Neural Network**: Deep learning model (TensorFlow/Keras)

### Model Performance
- **Best Model**: Neural Network with optimized hyperparameters
- **Validation Accuracy**: 82.5%
- **Features**: Age, Sex, Blood Pressure, Cholesterol, Na_to_K ratio
- **Drug Classes**: DrugY, drugA, drugB, drugC, drugX

### Prediction Pipeline
1. **Data Fetching**: Retrieves latest patient from database
2. **Preprocessing**: Applies trained preprocessor to input data
3. **Prediction**: Uses neural network model for drug classification
4. **Result Display**: Shows prediction with confidence metrics

## Project Structure

```
├── api/                          
│   ├── main.py                  
│   ├── db/                       
│   │   ├── postgres.py          
│   │   └── mongo.py             
│   └── models/                   
│       └── patient_models.py    
├── data/                         
│   └── drug200.csv              
├── models/                       
│   ├── models_training.ipynb    
│   ├── saved_models/            
│   └── metadata.json            
├── encoders/                     
│   └── preprocessor.pkl         
├── scripts/                      
│   ├── predict_latest_patient.py 
│   ├── load_mongodb_data.py     
│   └── load_relational_data.py  
├── diagram/                      
│   └── drug-db-schema--.png    
├── schema.sql                   
├── requirements.txt              
└── README.md                    
```

## Technical Details

### Database Features
- **Normalization**: 3NF compliant schema
- **Constraints**: Data validation and integrity checks
- **Triggers**: Automated logging on patient insertion
- **Stored Procedures**: Custom procedures for data management

### API Features
- **Input Validation**: Pydantic models for data validation
- **Error Handling**: Comprehensive error responses
- **Database Fallback**: Automatic PostgreSQL → MongoDB fallback
- **CORS Support**: Cross-origin resource sharing enabled

### Machine Learning Features
- **Feature Engineering**: Automated preprocessing pipeline
- **Model Selection**: Multiple algorithms with performance comparison
- **Hyperparameter Tuning**: Grid search optimization
- **Model Persistence**: Saved models for production use

## Dataset Information

**Source**: [Drug Classification Dataset](https://www.kaggle.com/datasets/prathamtripathi/drug-classification)

**Features**:
- Age: Patient age (15-74)
- Sex: Gender (M/F)
- BP: Blood pressure (HIGH/NORMAL/LOW)
- Cholesterol: Cholesterol level (HIGH/NORMAL)
- Na_to_K: Sodium to potassium ratio (6.0-40.0)

**Target**: Drug classification (DrugY, drugA, drugB, drugC, drugX)

## Deployment

### Local Development
```bash
# Start the API server
python -m uvicorn api.main:app --reload

# Run prediction script
python scripts/predict_latest_patient.py
```

**Team Members**:
- Excel Asaph
- Nicolle Marizani  
- Chance Karambizi
- Diana Ruzindana