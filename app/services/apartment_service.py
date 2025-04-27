from app.api.schemas import ApartmentsQuery, ApartmentCreate, ApartmentUpdate
from sqlalchemy.orm import Session
from app.database import models
from sqlalchemy import func
from geoalchemy2 import Geometry
from sqlalchemy import text

import requests


# Функция для геокодирования города через Nominatim
def geocode_city(city_name):
    base_url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": city_name,
        "format": "json",
    }

    response = requests.get(base_url, params=params, timeout=10)
    data = response.json()

    if data and len(data) > 0:
        city_coords = {
            "lat": float(data[0]["lat"]),
            "lng": float(data[0]["lon"])
        }
        return city_coords
    else:
        return None
def get_apartment(db: Session, apartment_id: int):
    return db.query(models.Apartment) \
        .filter(models.Apartment.id == apartment_id) \
        .first()


def get_apartments(db: Session, apartments_query: ApartmentsQuery):

    query = db.query(models.Apartment)

    if apartments_query.city_name is not None and apartments_query.radius is not None:
        city_coords = geocode_city(apartments_query.city_name)
        if city_coords is not None:
            latitude = city_coords["lat"]
            longitude = city_coords["lng"]
            location = func.ST_GeogFromText(f'POINT({latitude} {longitude})', type_=Geometry)
            query = query.filter(func.ST_DWithin(models.Apartment.location, location, apartments_query.radius))
            query = query.order_by(func.ST_Distance(models.Apartment.location, location))


    if apartments_query.city_name is None and apartments_query.latitude is not None and apartments_query.longitude \
            is not None and apartments_query.radius is not None:
        location = func.ST_GeogFromText(f'POINT({apartments_query.latitude} {apartments_query.longitude})', type_=Geometry)
        query = query.filter(func.ST_DWithin(models.Apartment.location, location, apartments_query.radius))
        query = query.order_by(func.ST_Distance(models.Apartment.location, location))

    total_items = query.count()

    query = query.offset(apartments_query.offset).limit(apartments_query.limit)

    apartments = query.all()

    return {
        "items": apartments,
        "total": total_items,
        "size": len(apartments),
    }


def get_my_apartments(db: Session, email: str):

    query = db.query(models.Apartment).filter(models.Apartment.publisher_email==email)

    total_items = query.count()

    res = query.all()

    return {
        "items": res,
        "total": total_items,
        "size": len(res),
    }

def add_apartment(db: Session, apartment: ApartmentCreate):
    db_item = models.Apartment(**apartment.model_dump())
    db_item.location = f'POINT({apartment.latitude} {apartment.longitude})'

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def update_apartment(db: Session, apartment_id: int, updated_apartment: ApartmentUpdate):
    db_apartment = db.query(models.Apartment).filter(models.Apartment.id == apartment_id).first()

    if db_apartment:
        for attr, value in updated_apartment.dict().items():
            setattr(db_apartment, attr, value)

        db_apartment.location = f'POINT({updated_apartment.latitude} {updated_apartment.longitude})'

        db.commit()
        return db_apartment

    return None


def delete_apartment(db: Session, apartment_id: int):
    result = db.query(models.Apartment) \
        .filter(models.Apartment.id == apartment_id) \
        .delete()
    db.commit()
    query = text("delete from favorite_items where apartment_id = :id;")
    db.execute(query, {"id": apartment_id})
    db.commit()
    query = text("delete from reservation where apartment_id = :id;")
    db.execute(query, {"id": apartment_id})
    db.commit()
    return result == 1
