from pydantic import BaseModel, conint, confloat, constr

class PatientIn(BaseModel):
    age: conint(ge=15, le=74)
    sex: constr(min_length=1, max_length=1, pattern="^[MF]$")
    bp: constr(min_length=3, max_length=6, pattern="^(HIGH|NORMAL|LOW)$")
    cholesterol: constr(min_length=4, max_length=6, pattern="^(HIGH|NORMAL)$")
    na_to_k: confloat(ge=6.0, le=40.0)
    drug: constr(min_length=5, max_length=6, pattern="^(DrugY|drugX|drugA|drugB|drugC)$")