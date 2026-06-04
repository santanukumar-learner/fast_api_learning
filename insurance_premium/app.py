from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Literal, Annotated
import pickle
import pandas as pd
import uvicorn


tier_1_cities = {"Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"}
tier_2_cities = {
    "Jaipur", "Chandigarh", "Indore", "Lucknow", "Patna", "Ranchi", "Visakhapatnam", "Coimbatore",
    "Bhopal", "Nagpur", "Vadodara", "Surat", "Rajkot", "Jodhpur", "Raipur", "Amritsar", "Varanasi",
    "Agra", "Dehradun", "Mysore", "Jabalpur", "Guwahati", "Thiruvananthapuram", "Ludhiana", "Nashik",
    "Allahabad", "Udaipur", "Aurangabad", "Hubli", "Belgaum", "Salem", "Vijayawada", "Tiruchirappalli",
    "Bhavnagar", "Gwalior", "Dhanbad", "Bareilly", "Aligarh", "Gaya", "Kozhikode", "Warangal",
    "Kolhapur", "Bilaspur", "Jalandhar", "Noida", "Guntur", "Asansol", "Siliguri"
}

app = FastAPI()

model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        with open("model.pkl", "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        # Fail early so you notice immediately
        raise RuntimeError(f"Failed to load model.pkl: {e}")


class UserInput(BaseModel):
    age: Annotated[int, Field(gt=0, lt=100, description="Age of the user")]
    weight: Annotated[float, Field(gt=0, lt=1000, description="Weight (kg)")]
    height: Annotated[float, Field(gt=0, lt=2.5, description="Height (meters)")]
    income_lpa: Annotated[float, Field(ge=0, description="Income in LPA")]
    smoker: Annotated[bool, Field(description="Whether the user smokes")]
    city: Annotated[str, Field(min_length=2, description="City of the user")]
    occupation: Annotated[
        Literal["retired", "freelancer", "student", "government_job",
                "business_owner", "unemployed", "private_job"],
        Field(description="Occupation of the user")
    ]

    @computed_field
    @property
    def bmi(self) -> float:
        return self.weight / (self.height ** 2)

    @computed_field
    @property
    def lifestyle_risk(self) -> str:
        if self.smoker and self.bmi > 30:
            return "high"
        elif self.smoker or self.bmi > 27:
            return "medium"
        return "low"

    @computed_field
    @property
    def age_group(self) -> str:
        if self.age < 25:
            return "young"
        elif self.age < 45:
            return "adult"
        elif self.age < 60:
            return "middle_aged"
        return "senior"

    @computed_field
    @property
    def city_tier(self) -> int:
        # normalize city (case-insensitive match)
        city_norm = self.city.strip().title()
        if city_norm in tier_1_cities:
            return 1
        elif city_norm in tier_2_cities:
            return 2
        return 3


@app.post("/predict")
def predict_premium(data: UserInput):
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    input_df = pd.DataFrame([{
        "bmi": data.bmi,  # ✅ fixed from bni -> bmi
        "age_group": data.age_group,
        "lifestyle_risk": data.lifestyle_risk,
        "city_tier": data.city_tier,
        "income_lpa": data.income_lpa,
        "occupation": data.occupation,
        "smoker": data.smoker,
    }])

    try:
        prediction = model.predict(input_df)[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    return JSONResponse(status_code=200, content={"prediction": float(prediction) if hasattr(prediction, "__float__") else prediction})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
