import json
import logging

from ..config import get_settings
from ..schemas import UserInput, WorkoutPlan

logger = logging.getLogger(__name__)


SYSTEM_INSTRUCTION = """
You are FitBuddy, a fitness-planning assistant. Generate safe, practical, beginner-friendly
fitness plans from the supplied profile. Do not diagnose medical conditions, prescribe treatment,
or recommend extreme dieting. Prefer gradual progression, recovery, correct form, and sensible
exercise substitutions. If a user has an injury, pregnancy, serious medical condition, chest pain,
dizziness, or other concerning symptoms, advise professional medical clearance rather than trying
to solve the condition in the workout plan.
""".strip()


def _demo_plan(user: UserInput) -> WorkoutPlan:
    focus_by_day = [
        "Full body foundation",
        "Lower body strength",
        "Cardio and core",
        "Active recovery",
        "Upper body strength",
        "Full body conditioning",
        "Mobility and recovery",
    ]
    exercises = {
        "Full body foundation": ["Bodyweight squat", "Incline push-up", "Glute bridge"],
        "Lower body strength": ["Squat", "Reverse lunge", "Calf raise"],
        "Cardio and core": ["Brisk walk", "Dead bug", "Bird dog"],
        "Active recovery": ["Easy walk", "Cat-cow", "Hip mobility"],
        "Upper body strength": ["Incline push-up", "Band row", "Shoulder press"],
        "Full body conditioning": ["Step-up", "Push-up", "Hip hinge"],
        "Mobility and recovery": ["Easy walk", "Hamstring stretch", "Thoracic rotation"],
    }
    days = []
    for index, focus in enumerate(focus_by_day, start=1):
        days.append(
            {
                "day": f"Day {index}",
                "focus": focus,
                "warmup": "5–8 minutes of easy movement and dynamic mobility.",
                "exercises": [
                    {"name": name, "sets": 3 if index not in (4, 7) else 2, "reps": "8–12", "rest": "60–90 seconds"}
                    for name in exercises[focus]
                ],
                "cooldown": "5 minutes of easy movement and comfortable stretching.",
            }
        )
    return WorkoutPlan(
        title=f"7-Day {user.goal.title()} Plan",
        summary=f"A {user.intensity}-intensity starter plan designed around {user.goal}.",
        days=days,
    )


async def generate_workout_gemini(user: UserInput) -> str:
    settings = get_settings()
    if settings.mock_ai or not settings.gemini_api_key:
        return _demo_plan(user).model_dump_json(indent=2)

    from google import genai
    from google.genai import types

    prompt = f"""
Create a personalized 7-day workout plan for:
Name: {user.username}
Age: {user.age}
Weight: {user.weight} kg
Goal: {user.goal}
Preferred intensity: {user.intensity}

Return exactly seven days. Each day must include a focus, warm-up, 1–8 exercises with sets,
reps or duration, and rest intervals, plus a cooldown/recovery instruction. Use sensible variation
and recovery. Do not include medical diagnoses or dangerous/extreme recommendations.
""".strip()

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.workout_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.5,
                max_output_tokens=5000,
                response_mime_type="application/json",
                response_schema=WorkoutPlan.model_json_schema(),
            ),
        )
        plan = WorkoutPlan.model_validate(json.loads(response.text))
        return plan.model_dump_json(indent=2)
    except Exception:
        logger.exception("Gemini workout generation failed")
        raise RuntimeError("The AI workout service could not generate a plan right now.")
