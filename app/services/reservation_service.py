import datetime
from typing import List, Tuple

from app.api.schemas import ReservationCreate, ReservationUpdate
from sqlalchemy.orm import Session
from app.database import models

def get_reservation_items(db: Session, user_email: str, limit: int = 1, offset: int = 0):
    total_items = db.query(models.Reservation) \
        .filter(models.Reservation.email == user_email) \
        .count()

    res = db.query(models.Reservation) \
        .filter(models.Reservation.email == user_email) \
        .offset(offset) \
        .limit(limit) \
        .all()

    return {
        "items": res,
        "total": total_items,
        "size": len(res),
    }

def get_reservations_by_apartment(db: Session, apartment_id: int, start_date, end_date):
    return db.query(models.Reservation).filter(
        models.Reservation.apartment_id == apartment_id,
        models.Reservation.arrival_date <= end_date,
        models.Reservation.departure_date >= start_date
    ).all()


def get_reserved_periods_trimmed(
    db: Session, apartment_id: int, start_date, end_date
) -> List[Tuple[str, datetime.date, datetime.date]]:
    reservations = db.query(models.Reservation).filter(
        models.Reservation.apartment_id == apartment_id,
        models.Reservation.arrival_date < end_date,
        models.Reservation.departure_date > start_date
    ).order_by(models.Reservation.arrival_date).all()

    return [
        (
            r.email,
            max(r.arrival_date, start_date),
            min(r.departure_date, end_date)
        )
        for r in reservations
    ]


def get_available_periods(db: Session, apartment_id: int, start_date, end_date) -> List[Tuple[datetime.date, datetime.date]]:
    reservations = db.query(models.Reservation).filter(
        models.Reservation.apartment_id == apartment_id,
        models.Reservation.arrival_date < end_date,
        models.Reservation.departure_date > start_date
    ).order_by(models.Reservation.arrival_date).all()

    available_periods = []
    current_start = start_date

    for reservation in reservations:
        if reservation.arrival_date > current_start:
            available_periods.append((current_start, reservation.arrival_date))
        current_start = max(current_start, reservation.departure_date)

    if current_start < end_date:
        available_periods.append((current_start, end_date))

    return available_periods



def get_reservation_item(db: Session, item_id: int):
    return db.query(models.Reservation) \
        .filter(models.Reservation.id == item_id) \
        .first()


async def add_reservation_item(db: Session, item: ReservationCreate):

    db_item = models.Reservation(**item.model_dump())

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def update_reservation_item(db: Session, item_id: int, updated_item: ReservationUpdate):
    result = db.query(models.Reservation) \
        .filter(models.Reservation.id == item_id) \
        .update(updated_item.dict())
    db.commit()

    if result == 1:
        return updated_item
    return None


def delete_reservation_item(db: Session, item_id: int):
    result = db.query(models.Reservation) \
        .filter(models.Reservation.id == item_id) \
        .delete()
    db.commit()
    return result == 1
