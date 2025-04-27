from datetime import date, datetime
from typing import Generic, Optional, Sequence, TypeVar
from uuid import UUID
from pydantic import BaseModel, EmailStr
import uuid
from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate

# User Service Schemas
class GroupCreate(BaseModel):
    name: str

    class Config:
        from_attributes = True

class GroupRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class GroupUpdate(BaseModel):
    name: str

    class Config:
        from_attributes = True

class GroupUpsert(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class UserRead(BaseUser[uuid.UUID]):
    username: Optional[str]  = None
    group_id: Optional[int]  = None

class UserCreate(BaseUserCreate):
    username: Optional[str]  = None
    group_id: Optional[int]  = None

class UserUpdate(BaseUserUpdate):
    username: Optional[str]  = None
    group_id: Optional[int] = None

# Apartment Service Schemas
class BaseApartment(BaseModel):
    title: str
    address: str
    rooms: int
    area: int
    latitude: float
    longitude: float
    image1: Optional[str] = None
    image2: Optional[str] = None
    image3: Optional[str] = None
    image4: Optional[str] = None
    image5: Optional[str] = None
    image6: Optional[str] = None

class Apartment(BaseApartment):
    id: int
    publisher_email: EmailStr

    class Config:
        from_attributes = True

class ApartmentCreate(BaseApartment):
    publisher_email: EmailStr

class ApartmentUpdate(BaseApartment):
    publisher_email: EmailStr

class ApartmentsQuery(BaseModel):
    city_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    radius: Optional[float]
    limit: int = 1
    offset: int = 0

class PaginatedApartmentResponse(BaseModel):
    items: list[Apartment]
    size: Optional[int]
    total: Optional[int]

# Reservation Service Schemas
class BaseReservation(BaseModel):
    arrival_date: date
    departure_date: date
    apartment_id: int

class Reservation(BaseReservation):
    id: int

    class Config:
        from_attributes = True

class ReservationCreate(BaseReservation):
    email: EmailStr

class ReservationUpdate(BaseReservation):
    email: EmailStr

class PaginatedReservation(BaseModel):
    items: list[Reservation]
    size: Optional[int]
    total: Optional[int]

# Review Service Schemas
class ReviewBase(BaseModel):
    apartment_id: int
    title: str
    description: str

class ReviewCreate(ReviewBase):
    user_email: EmailStr

class ReviewUpdate(BaseModel):
    title: str
    description: str

class Review(ReviewBase):
    id: UUID

# Favorite Service Schemas
class BaseFavoriteItem(BaseModel):
    apartment_id: int

class FavoriteItem(BaseFavoriteItem):
    id: int

    class Config:
        from_attributes = True

class PaginatedFavoriteItemsResponse(BaseModel):
    items: list[FavoriteItem]
    size: Optional[int]
    total: Optional[int]

class FavoriteItemCreate(BaseFavoriteItem):
    user_email: EmailStr

class FavoriteItemDelete(BaseFavoriteItem):
    pass

# Notification Service Schemas
class ApartmentData(BaseModel):
    title: str
    address: str

    class Config:
        from_attributes = True

class ReservationNotification(BaseModel):
    email: EmailStr
    arrival_date: datetime
    departure_date: datetime
    apartment_data: ApartmentData

    class Config:
        from_attributes = True

class ReviewNotification(BaseModel):
    email: EmailStr
    title: str
    description: str

    class Config:
        from_attributes = True