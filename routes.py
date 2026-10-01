import json
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import get_settings
from .crud import delete_user, get_all_users, get_user, save_user, update_plan
from .database import get_db
from .schemas import FeedbackRequest, UserInput
from .services.gemini_flash_generator import generate_nutrition_tip_with_flash
from .services.gemini_generator import generate_workout_gemini
from .services.updated_plan import update_workout_plan

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
router = APIRouter()
api_router = APIRouter(prefix="/api")


def _plan_for_template(raw_plan: str) -> dict:
    try:
        return json.loads(raw_plan)
    except json.JSONDecodeError:
        return {"title": "Workout Plan", "summary": "", "days": []}


def _error_context(request: Request, message: str):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"error": message},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_input = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )
        if get_user(db, user_input.user_id):
            return _error_context(request, "That user ID already exists. Choose another one.")

        workout_plan = await generate_workout_gemini(user_input)
        nutrition_tip = await generate_nutrition_tip_with_flash(user_input)
        record = save_user(db, user_input, workout_plan, nutrition_tip)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": record,
                "workout_plan": _plan_for_template(workout_plan),
                "nutrition_tip": nutrition_tip,
                "is_updated": False,
                "message": None,
            },
        )
    except (ValueError, RuntimeError) as exc:
        db.rollback()
        return _error_context(request, str(exc))
    except Exception:
        db.rollback()
        return _error_context(request, "Something went wrong while generating your plan.")


@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id.strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        payload = FeedbackRequest(user_id=user_id, feedback=feedback)
        revised = await update_workout_plan(user.original_plan, payload.feedback)
        update_plan(db, user, revised, payload.feedback)
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "workout_plan": _plan_for_template(revised),
                "nutrition_tip": user.nutrition_tip,
                "is_updated": True,
                "message": "Your workout plan has been updated using your feedback.",
            },
        )
    except (ValueError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.admin_key:
        supplied = request.query_params.get("key")
        if supplied != settings.admin_key:
            raise HTTPException(status_code=401, detail="Admin key required")
    users = get_all_users(db)
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": users, "admin_key": settings.admin_key})


@router.post("/admin/users/{user_id}/delete")
async def admin_delete_user(user_id: str, request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.admin_key and request.query_params.get("key") != settings.admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if not delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return RedirectResponse(url="/view-all-users", status_code=status.HTTP_303_SEE_OTHER)


@api_router.get("/health")
async def health():
    return {"status": "ok"}


@api_router.post("/generate-workout")
async def api_generate_workout(payload: UserInput, db: Session = Depends(get_db)):
    if get_user(db, payload.user_id):
        raise HTTPException(status_code=409, detail="User ID already exists")
    try:
        plan = await generate_workout_gemini(payload)
        tip = await generate_nutrition_tip_with_flash(payload)
        record = save_user(db, payload, plan, tip)
        return {
            "user": record,
            "workout_plan": _plan_for_template(plan),
            "nutrition_tip": tip,
        }
    except (ValueError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.post("/submit-feedback")
async def api_submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    user = get_user(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        revised = await update_workout_plan(user.original_plan, payload.feedback)
        update_plan(db, user, revised, payload.feedback)
        return {"user": user, "workout_plan": _plan_for_template(revised)}
    except (ValueError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@api_router.get("/users")
async def api_users(db: Session = Depends(get_db)):
    return get_all_users(db)


@api_router.get("/users/{user_id}")
async def api_user(user_id: str, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
