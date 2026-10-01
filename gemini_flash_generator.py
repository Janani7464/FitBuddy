import json
import logging

from ..config import get_settings
from ..schemas import NutritionTip, UserInput

logger = logging.getLogger(__name__)


def _demo_tip(user: UserInput) -> NutritionTip:
    tips = {
        "weight loss": "Build meals around vegetables, a protein source, whole-food carbohydrates, and water; aim for gradual, sustainable changes.",
        "muscle gain": "Include a protein-rich food at each meal and combine it with enough total food, carbohydrates, hydration, and recovery to support training.",
        "general wellness": "Prioritize regular meals, varied whole foods, adequate hydration, and consistent sleep to support everyday activity.",
        "flexibility": "Stay hydrated and include protein-rich foods, fruits, vegetables, and regular meals to support training and recovery.",
    }
    return NutritionTip(tip=tips[user.goal])


async def generate_nutrition_tip_with_flash(user: UserInput) -> str:
    settings = get_settings()
    if settings.mock_ai or not settings.gemini_api_key:
        return _demo_tip(user).tip

    from google import genai
    from google.genai import types

    prompt = f"Give one concise, practical nutrition or recovery tip for a person pursuing {user.goal} with {user.intensity} workout intensity. Avoid extreme diets and medical claims."
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.nutrition_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=250,
                response_mime_type="application/json",
                response_schema=NutritionTip.model_json_schema(),
            ),
        )
        return NutritionTip.model_validate(json.loads(response.text)).tip
    except Exception:
        logger.exception("Gemini nutrition generation failed")
        raise RuntimeError("The AI nutrition service could not generate a tip right now.")
