from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Literal

class FlightInput(BaseModel):
    type: Literal["arrival", "departure", "intercity"]
    city: Optional[str] = None
    from_city: Optional[str] = None
    to_city: Optional[str] = None
    date: str
    flight_number: str


class CreateTripRequest(BaseModel):
    country: str
    cities: list[str]
    start_date: str
    end_date: str
    travel_style: str
    interests: list[str]
    budget: str
    must_include: list[str]
    arrival_flight_number: str | None = None
    departure_flight_number: str | None = None


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str
    name: str

    
class ChatRequest(BaseModel):
    message: str

class WeatherReplaceRequest(BaseModel):
    day: int
    activity_index: int
