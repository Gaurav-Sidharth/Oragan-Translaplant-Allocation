from datetime import datetime
from pydantic import BaseModel, Field


class HospitalIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class DonorIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    blood_type: str


class OrganIn(BaseModel):
    donor_id: int
    donor_hospital_id: int | None = None
    organ_type: str = Field(min_length=1, max_length=100)
    blood_type: str
    viability_seconds: int = Field(gt=0, le=2_592_000)


class RecipientIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    organ_type: str = Field(min_length=1, max_length=100)
    blood_type: str
    urgency_score: int = Field(ge=1, le=10)
    waiting_days: int = Field(ge=0)
    hospital_id: int


class DistanceIn(BaseModel):
    from_hospital_id: int
    to_hospital_id: int
    distance_km: float = Field(ge=0)


class ClaimIn(BaseModel):
    organ_id: int
    recipient_id: int
    hospital_id: int


class EventOut(BaseModel):
    event_id: int
    event_type: str
    entity_type: str
    entity_id: int | None
    hospital_id: int | None
    payload: dict
    created_at: datetime
