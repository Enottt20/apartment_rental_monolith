from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.schemas import ReviewUpdate, ReviewCreate
from app.database import models
from typing import Optional
from app import config

cfg: config.Config = config.load_config()


async def fetch_apartment_email(db: Session, apartment_id: int):
    return db.query(models.Apartment) \
        .filter(models.Apartment.id == apartment_id) \
        .first()


def get_reviews_by_apartment_id(db: Session, apartment_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Review) \
        .filter(models.Review.apartment_id == apartment_id) \
        .offset(skip).limit(limit).all()


def get_review_by_uid(db: Session, uid: int) -> Optional[models.Review]:
    return db.query(models.Review).filter(models.Review.id == uid).first()


def update_review_by_uid(db: Session, uid: int, review_update: ReviewUpdate):
    review = db.query(models.Review).filter(models.Review.id == uid).first()

    if review is None:
        return None

    review.title = review_update.title
    review.description = review_update.description

    db.commit()
    db.refresh(review)
    return review


def remove_review_by_uid(db: Session, uid: int):
    review = db.query(models.Review).filter(models.Review.id == uid).first()

    if review is None:
        return JSONResponse(status_code=404, content={"message": "review not found"})

    db.delete(review)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Deleted"})


async def add_review(db: Session, review: ReviewCreate):
    existing_review = db.query(models.Review).filter(
        models.Review.apartment_id == review.apartment_id,
        models.Review.user_email == review.user_email
    ).first()

    if existing_review:
        return None

    apartment = await fetch_apartment_email(db, review.apartment_id)
    if not apartment:
        return JSONResponse(status_code=404, content={"message": "apartment not found"})

    new_review = models.Review(**review.model_dump())
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review