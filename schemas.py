from typing import Literal

from pydantic import BaseModel, Field, field_validator


Goal = Literal["weight loss", "muscle gain", "general wellness", "flexibility"]
Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    username: str = Field(min_length=2, max_length=120)
    user_id: str = Field(min_length=2, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=13, le=100)
    weight: float = Field(gt=20, le=500)
    goal: Goal
    intensity: Intensity

    @field_validator("username", "user_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=80)
    feedback: str = Field(min_length=3, max_length=1500)


class Exercise(BaseModel):
    name: str
    sets: int = Field(ge=1, le=10)
    reps: str
    rest: str


class WorkoutDay(BaseModel):
    day: str
    focus: str
    warmup: str
    exercises: list[Exercise] = Field(min_length=1, max_length=8)
    cooldown: str


class WorkoutPlan(BaseModel):
    title: str
    summary: str
    days: list[WorkoutDay] = Field(min_length=7, max_length=7)


class NutritionTip(BaseModel):
    tip: str


class UserResponse(BaseModel):
    id: int
    user_id: str
    username: str
    age: int
    weight: float
    goal: str
    intensity: str
    original_plan: str
    updated_plan: str | None
    nutrition_tip: str
    feedback: str | None

    model_config = {"from_attributes": True}
