from pydantic import BaseModel, EmailStr, AnyUrl, Field, field_validator
from typing import Annotated


class Patient(BaseModel):
    name:Annotated[str, Field(max_length=50, title="name of the patient", description="Give the name of the patient in less than 50 chars")]
    email : EmailStr
    age:int = Field(gt=18, le=50)
    weight: Annotated[float, Field(gt=0, le=300, strict=True)]
    @field_validator('email')
    @classmethod
    def email_validator(cls, value):
        valid_domains = ['hdfc.com', 'nitrkl.ac.in']
        domain_name = value.split('@')[-1]

        if domain_name not in valid_domains:
            raise ValueError("Not a valid domain")
        return value
    
    @field_validator('name')
    @classmethod
    def capital(cls, value):
        name = value.upper()
        return name

    @field_validator('age', mode='after')
    @classmethod
    def validate_date(cls, value):
        if 0 < value < 100:
            return value 
        else:
            raise ValueError("Age should be in range 0 to 100")

    

def insert_patient_data(patient: Patient):
    print(patient.name)
    print(patient.age)
    print('inserted')


patient_info = {'name' : "Santanu", "email":"santanu@nitrkl.ac.in", "age" : 22, 'weight':72.5}

patient1 = Patient(**patient_info)
insert_patient_data(patient1)