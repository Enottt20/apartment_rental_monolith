from app.api.schemas import FavoriteItemCreate
from sqlalchemy.orm import Session
from app.database import models


def get_favorite_items_by_user_email(db: Session, user_email: str, limit: int = 1, offset: int = 0):
    total_items = db.query(models.FavoriteItem) \
        .filter(models.FavoriteItem.user_email == user_email) \
        .count()

    res = db.query(models.FavoriteItem) \
        .filter(models.FavoriteItem.user_email == user_email) \
        .offset(offset) \
        .limit(limit) \
        .all()

    return {
        "items": res,
        "total": total_items,
        "size": len(res),
    }


def get_favorite_item_by_id(db: Session, item_id: int):
    return db.query(models.FavoriteItem) \
        .filter(models.FavoriteItem.id == item_id) \
        .first()


def add_favorite_item(db: Session, item: FavoriteItemCreate):

    # Проверка, есть ли уже такой товар в избранном у пользователя
    existing_favorite = db.query(models.FavoriteItem).filter(
        models.FavoriteItem.user_email == item.user_email,
        models.FavoriteItem.apartment_id == item.apartment_id
    ).first()

    if existing_favorite:
        # Если товар уже в избранном, не добавляем его повторно
        return existing_favorite

    db_item = models.FavoriteItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def delete_favorite_item(db: Session, item_id: int):
    db_favorite_item = (
        db.query(models.FavoriteItem)
        .filter(
            models.FavoriteItem.id == item_id
        )
        .delete()
    )
    db.commit()
    return db_favorite_item == 1
