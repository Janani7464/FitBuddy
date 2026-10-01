# FitBuddy – AI Fitness Plan Generator

FitBuddy is a FastAPI + Jinja2 + SQLite web application that generates personalized 7-day workout plans and concise nutrition/recovery tips with Google Gemini. Users can submit feedback to regenerate an updated plan, while a coach/admin view can inspect stored users and both plan versions.

The project follows the supplied documentation's architecture: HTML/Jinja2 frontend, FastAPI routing, Gemini-powered AI layer, and SQLAlchemy/SQLite persistence. The original documentation named Gemini 1.5 Pro and Gemini Flash; the implementation keeps the Pro/Flash responsibility split but makes the model IDs configurable because Google's current SDK guidance uses the `google-genai` package and current model IDs.

## Features

- Personalized 7-day workout plan generation
- Goal options: weight loss, muscle gain, general wellness, flexibility
- Intensity options: low, medium, high
- Nutrition/recovery tip generation
- Feedback-based plan regeneration
- SQLite persistence with SQLAlchemy 2.x
- Browser UI with Jinja2 templates
- JSON API plus automatic OpenAPI/Swagger docs
- Admin/coach dashboard
- Optional admin-key protection
- Local demo fallback when `GEMINI_API_KEY` is not configured
- Automated pytest coverage for the main user flows

## Project structure

```text
fitbuddy/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_generator.py
│   │   ├── gemini_flash_generator.py
│   │   └── updated_plan.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── result.html
│   │   └── all_users.html
│   └── static/
│       ├── css/styles.css
│       └── js/app.js
├── data/
├── tests/test_app.py
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 1. VS Code setup on Windows

Install Python 3.11 or newer and VS Code. Open the `fitbuddy` folder in VS Code.

Create a virtual environment in the VS Code terminal:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

Select the `.venv` interpreter in VS Code: `Ctrl+Shift+P` → `Python: Select Interpreter`.

## 2. Configure Gemini

Copy `.env.example` to `.env`.

```powershell
Copy-Item .env.example .env
```

Put your Google AI Studio API key in `.env`:

```dotenv
GEMINI_API_KEY=your_real_key_here
```

The defaults use `gemini-3.8-flash` for both generation paths. You can change:

```dotenv
WORKOUT_MODEL=gemini-3.8-flash
NUTRITION_MODEL=gemini-3.8-flash
```

If you want to run the whole UI without consuming Gemini API calls, set:

```dotenv
MOCK_AI=true
```

With no API key at all, the application also falls back to deterministic demo responses, so the frontend, database, routes, and tests remain runnable.

## 3. Run the application

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000 — FitBuddy UI
- http://127.0.0.1:8000/docs — Swagger API docs
- http://127.0.0.1:8000/redoc — ReDoc
- http://127.0.0.1:8000/view-all-users — admin/coach view

The SQLite database is created automatically at `data/fitbuddy.db` on first startup.

## 4. Test the application

Run all tests:

```powershell
pytest
```

The tests use a separate SQLite database and force local mock AI responses, so they do not require a Gemini API key.

You can also test the API interactively from `/docs`.

### Example API request

`POST /api/generate-workout`

```json
{
  "username": "Alex",
  "user_id": "alex01",
  "age": 25,
  "weight": 70,
  "goal": "muscle gain",
  "intensity": "medium"
}
```

Then update the plan with:

`POST /api/submit-feedback`

```json
{
  "user_id": "alex01",
  "feedback": "Add more cardio and include another rest day."
}
```

## 5. Optional admin protection

For a simple local demo, `/view-all-users` is open. To require a key, put this in `.env`:

```dotenv
ADMIN_KEY=change-this-local-key
```

Then visit:

```text
http://127.0.0.1:8000/view-all-users?key=change-this-local-key
```

Delete operations use the same query-string key.

For production, replace this lightweight mechanism with proper authentication, authorization, CSRF protection, and secure secret management.

## 6. Docker

Build and run:

```powershell
docker build -t fitbuddy .
docker run --rm -p 8000:8000 --env-file .env fitbuddy
```

Open http://127.0.0.1:8000.

For persistent database storage with Docker, mount the `data` directory as a volume.

## Implementation notes

### AI layer

`app/services/gemini_generator.py` handles structured workout generation. `app/services/gemini_flash_generator.py` generates the concise nutrition/recovery tip. `app/services/updated_plan.py` sends the original structured plan and user feedback back to Gemini and validates the returned JSON with Pydantic.

Structured output is used instead of relying on free-form text formatting. This makes the seven-day plan predictable and directly renderable in Jinja2.

### Persistence

The `users` table stores the requested user fields, the original generated plan, optional updated plan, feedback, and nutrition tip. Both original and updated plans are retained so the admin page can compare versions.

### Safety boundary

FitBuddy is designed as a wellness planning demo, not a medical system. The AI prompt explicitly avoids diagnosis, treatment, and extreme exercise/diet recommendations. The UI also tells users to stop for concerning symptoms and seek appropriate professional advice.

### Production hardening checklist

Before deploying publicly, add:

- Real authentication and role-based authorization
- CSRF protection for browser forms
- Rate limiting and abuse controls for AI endpoints
- HTTPS and secure cookie/session handling if sessions are added
- Secret management instead of a checked-in `.env`
- Database migrations with Alembic
- Structured application logging and monitoring
- AI request timeouts/retries with bounded backoff
- Per-user authorization so users cannot read another user's plan by ID
- Privacy policy and appropriate data retention/deletion controls
- More comprehensive domain-specific fitness validation
