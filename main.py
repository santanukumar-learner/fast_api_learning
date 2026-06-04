from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel, field_validator, Field, computed_field
import json
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Optional


def load_data():
    with open("patient.json", "r") as f:
        data = json.load(f)
    return data
def save_data(data):
    with open('patient.json', 'w') as f:
        json.dump(data, f)

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", examples=['p001'])]
    name:Annotated[str, Field(..., description='name of the patient')]
    city:str
    age:Annotated[int, Field(gt=0, lt=120)]
    gender:Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the patient')]
    height:Annotated[float, Field(..., description="height of the patient")]
    weight:float

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height**2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Under weight"
        elif self.bmi < 25:
            return "Normal"
        else:
            return "over weight"
        
class PatientUpdate(BaseModel): # new pydantic class created because the old one can't used to update as it will require all the values as necesity while update require only those whhich we want to update
    name:Annotated[Optional[str], Field(default=None)]
    city:Annotated[Optional[str], Field(default=None)]
    age:Annotated[Optional[int], Field(gt=0, lt=120)]
    gender:Annotated[Optional[Literal['male', 'female', 'others']], Field(default=None)]
    height:Annotated[Optional[float], Field(default=None)]
    weight:Annotated[Optional[float], Field(default=None)]            

app = FastAPI()
@app.get("/")
def view():
    data = load_data()
    return f"Welcome to the patient management system"

@app.get("/patient/{patient_id}")
def view_patient(patient_id:str = Path(..., description="The ID of the patient"), example="P001"):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    else:
        return {"error":"Patient not found"}
    
@app.get('/sort')
def sort_patients(sort_by:str = Query(..., description="The field to sort by"), sort_order:str = Query('asc', description="The order to sort by")):
    valid_fields = ['height', 'weight', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field select from {valid_field}")
    if sort_order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid sort order select from ['asc', 'desc']")
    data = load_data()

    sorted_data = sorted(data.values(), key=lambda x: x[sort_by], reverse=sort_order == 'desc')

    return sorted_data

@app.post("/create")
def create_patient(patient:Patient):
    data = load_data()
    if patient.id in data:
        raise HTTPException(status_code=400, detail='patient already exist')
    data[patient.id] = patient.model_dump(exclude=['id'])
    save_data(data)
    return JSONResponse(status_code=201, content={'messege': "patient created successfully"})

@app.put('/update/{patient_id}')
def update_patient_info(patient_id:str, patient_update:PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient does not exist')
    existing_patient_info = data[patient_id]
    updated_patient_info = patient_update.model_dump(exclude_unset=True) # this exclude unset will not recieve those which not given otherwise we will recieve the None values where we are not recieving any update values
    for key, value in update_patient_info.items():
        existing_patient_info[key] = value

    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)
    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')

    data[patient_id] = existing_patient_info
    save_data()

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={'message':'patient deleted'})



    