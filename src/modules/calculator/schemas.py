"""Calculator module Pydantic schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.core.settings import settings


class Gender(str, Enum):
    """Gender enum for BMR calculation."""

    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    """Activity level enum with standard multipliers."""

    SEDENTARY = "sedentary"  # 1.2
    LIGHT = "light"  # 1.375
    MODERATE = "moderate"  # 1.55
    ACTIVE = "active"  # 1.725
    VERY_ACTIVE = "very_active"  # 1.9


class Goal(str, Enum):
    """Fitness goal enum."""

    WEIGHT_LOSS = "weight_loss"
    MAINTENANCE = "maintenance"
    MUSCLE_GAIN = "muscle_gain"


class CalculateRequest(BaseModel):
    """Request schema for calorie calculation."""

    gender: Gender = Field(..., description="User gender (male/female)")
    age: int = Field(..., description="User age in years", ge=settings.calculator_min_age, le=settings.calculator_max_age)
    weight_kg: float = Field(..., description="User weight in kilograms", ge=settings.calculator_min_weight_kg, le=settings.calculator_max_weight_kg)
    height_cm: float = Field(..., description="User height in centimeters", ge=settings.calculator_min_height_cm, le=settings.calculator_max_height_cm)
    activity_level: ActivityLevel = Field(..., description="Physical activity level")
    goal: Goal = Field(..., description="Fitness goal")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "gender": "female",
                "age": 25,
                "weight_kg": 65,
                "height_cm": 170,
                "activity_level": "moderate",
                "goal": "weight_loss",
            }
        }


class TariffInfo(BaseModel):
    """Simplified tariff information for calculator response."""

    id: str
    name: str
    description: Optional[str]
    calories: Optional[int]
    base_price: int


class CalculateResponse(BaseModel):
    """Response schema for calorie calculation."""

    recommended_calories: int = Field(..., description="Recommended daily calorie intake")
    tariff: Optional[TariffInfo] = Field(None, description="Recommended tariff plan")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "recommended_calories": 1711,
                "tariff": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Fit Start",
                    "description": "Starter plan for weight loss",
                    "calories": 1650,
                    "base_price": 4900,
                },
            }
        }
