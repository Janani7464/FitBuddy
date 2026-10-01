from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User
from .schemas import UserInput


def save_user(db: Session, user: UserInput, original_plan: str, nutrition_tip: str) -> User:
    existing = db.scalar(select(User).where(User.user_id == user.user_id))
    if existing:
        raise ValueError("That user ID already exists. Use a different user ID.")

    record = User(
        user_id=user.user_id,
        username=user.username,
        age=user.age,
        weight=user.weight,
        goal=user.goal,
        intensity=user.intensity,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


def update_plan(db: Session, user: User, revised_plan: str, feedback: str) -> User:
    user.updated_plan = revised_plan
    user.feedback = feedback
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: str) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
