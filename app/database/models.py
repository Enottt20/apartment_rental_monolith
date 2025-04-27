# apartment_rental_monolith/app/database/models.py
from sqlalchemy import Column, Integer, String, Float, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, mapped_column
from geoalchemy2 import Geometry
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from uuid import uuid4
from app.database.base import Base
from app.database import async_base
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTableUUID, SQLAlchemyUserDatabase

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import mapped_column, relationship


class Group(async_base.BASE):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String)


class User(SQLAlchemyBaseUserTableUUID, async_base.BASE):
    __table_args__ = {'schema':  async_base.SCHEMA}

    username = Column(String(length=128), nullable=True)
    group_id = mapped_column(ForeignKey("group.id"))
    group = relationship("Group", uselist=False)


async def get_user_db(session: AsyncSession = Depends(async_base.get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String, index=True)
    address = Column(String, index=True)
    rooms = Column(Integer)
    area = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(Geometry("POINT", srid=4326))
    publisher_email = Column(String)

    image1 = Column(Text)
    image2 = Column(Text)
    image3 = Column(Text)
    image4 = Column(Text)
    image5 = Column(Text)
    image6 = Column(Text)


class Reservation(Base):
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String)
    arrival_date = Column(Date)
    departure_date = Column(Date)
    apartment_id = Column(Integer)


class Review(Base):
    __tablename__ = 'review'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    apartment_id = Column(Integer)
    user_email = Column(String)

    def __str__(self):
        return (f"title={self.title}, description={self.description}"
                f"apartment_id={self.apartment_id}, user_email={self.user_email}")


class FavoriteItem(Base):
    __tablename__ = 'favorite_items'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    apartment_id = Column(Integer)
    user_email = Column(String)