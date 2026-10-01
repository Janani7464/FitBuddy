import json
import logging

from ..config import get_settings
from ..schemas import WorkoutPlan

logger = logging.getLogger(__name__)


async def update_workout_plan(original_plan: str, feedback: str) -> str:
    settings = get_settings()
    try:
        original = WorkoutPlan.model_validate_json(original_plan)
    except Exception as exc:
        raise ValueError("The stored workout plan is not valid structured data.") from exc

    if settings.mock_ai or not settings.gemini_api_key:
        updated = original.model_copy(deep=True)
        updated.summary += f" Updated using feedback: {feedback.strip()}"
        return updated.model_dump_json(indent=2)

    from google import genai
    from google.genai import types

    prompt = f"""
Here is the existing FitBuddy plan:
{original.model_dump_json(indent=2)}

User feedback:
{feedback}

Return the complete revised 7-day plan. Apply the feedback where reasonable while keeping a
balanced schedule, recovery, safe progression, and the same structured JSON shape.
""".strip()

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.workout_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=5000,
                response_mime_type="application/json",
                response_schema=WorkoutPlan.model_json_schema(),
            ),
        )
        return WorkoutPlan.model_validate(json.loads(response.text)).model_dump_json(indent=2)
    except Exception:
        logger.exception("Gemini plan update failed")
        raise RuntimeError("The AI workout service could not update the plan right now.")
