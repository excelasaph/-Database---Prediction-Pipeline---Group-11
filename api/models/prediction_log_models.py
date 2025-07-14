from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PredictionLogIn(BaseModel):
    patient_id: int 
    predicted_drug: str
    model_type: str
    prediction_time: Optional[datetime] = None
    actual_drug: Optional[str] = None 
    prediction_success: Optional[bool] = None
    db_used: str  # "postgresql"/"mongodb"
