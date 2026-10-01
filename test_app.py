import os
from pathlib import Path

TEST_DB = Path(__file__).resolve().parent / "test_fitbuddy.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["MOCK_AI"] = "true"
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    if TEST_DB.exists():
        TEST_DB.unlink()
    for suffix in ("-shm", "-wal"):
        p = Path(str(TEST_DB) + suffix)
        if p.exists():
            p.unlink()


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "Build your plan" in response.text


def test_generate_workout_form_creates_user():
    response = client.post(
        "/generate-workout",
        data={
            "username": "Alex",
            "user_id": "alex01",
            "age": "25",
            "weight": "70",
            "goal": "muscle gain",
            "intensity": "medium",
        },
    )
    assert response.status_code == 200
    assert "Alex's week" in response.text
    assert "Day 1" in response.text


def test_duplicate_user_is_rejected():
    response = client.post(
        "/generate-workout",
        data={
            "username": "Another Alex",
            "user_id": "alex01",
            "age": "25",
            "weight": "70",
            "goal": "muscle gain",
            "intensity": "medium",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.text


def test_feedback_updates_plan():
    response = client.post(
        "/submit-feedback",
        data={"user_id": "alex01", "feedback": "Add more cardio and another rest day."},
    )
    assert response.status_code == 200
    assert "updated" in response.text.lower()


def test_json_api_lists_user():
    response = client.get("/api/users/alex01")
    assert response.status_code == 200
    assert response.json()["user_id"] == "alex01"


def test_validation_rejects_invalid_age():
    response = client.post(
        "/api/generate-workout",
        json={
            "username": "Young",
            "user_id": "young1",
            "age": 10,
            "weight": 50,
            "goal": "general wellness",
            "intensity": "low",
        },
    )
    assert response.status_code == 422
