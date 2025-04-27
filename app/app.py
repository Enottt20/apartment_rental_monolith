import typing, logging
import datetime
from typing import Tuple, List

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import BaseApartment, ApartmentUpdate, ApartmentCreate, PaginatedApartmentResponse, \
    ApartmentsQuery, BaseFavoriteItem, FavoriteItemCreate, PaginatedFavoriteItemsResponse, ReservationCreate, \
    PaginatedReservation, BaseReservation, ReviewBase, ReviewCreate, ReviewUpdate, Apartment, FavoriteItem, Reservation, Review

from app.auth import AuthInitializer, include_routers
import json
from fastapi.middleware.cors import CORSMiddleware
from app import config
from app.api import schemas
from app.database.models import User
# from app.database.models import Apartment, FavoriteItem, Reservation, Review
from app.services import apartment_service, favorite_service, reservation_service, review_service, user_service
from app.database import async_base, base
from app.database.base import DB_INITIALIZER
from fastapi import FastAPI, Depends, Query
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import typing
import logging
from fastapi import FastAPI, Depends, Request
import jwt
from fastapi.middleware.cors import CORSMiddleware



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=20,
    format="%(levelname)-9s %(message)s"
)

logger.info("Configuration loading...")
cfg: config.Config = config.load_config()
logger.info(
    'Service configuration loaded:\n' +
    f'{cfg.model_dump_json(by_alias=True, indent=4)}'
)

# Создание приложения FastAPI
app = FastAPI(
    version='0.0.1',
    title='apartment service'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth = AuthInitializer()
auth.initializer(cfg.jwt_secret)

include_routers(app, auth.get_auth_backend(), auth.get_fastapi_users())


@app.on_event("startup")
async def on_startup():
    await async_base.DB_INITIALIZER.init_db(
        str(cfg.POSTGRES_DSN_ASYNC)
    )

    groups = [
    {
        "id": 1,
        "name": "Customer"
    },
    {
        "id": 2,
        "name": "Seller"
    },
    {
        "id": 3,
        "name": "Admin"
    }
]

    if groups is not None:
        async for session in async_base.get_async_session():
            for group in groups:
                await user_service.upsert_group(
                    session, schemas.GroupUpsert(**group)
                )
    else:
        logger.error('Конфигурация с группами не была загружена')

SessionLocal = DB_INITIALIZER.init_database(str(cfg.POSTGRES_DSN))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def extract_email_data(request: Request) -> str:
    try:
        if 'authorization' in request.headers:
            token = request.headers['authorization'].split(' ')[1]
            data = jwt.decode(token, cfg.jwt_secret, algorithms=["HS256"], audience=["fastapi-users:auth"])
            return data.get("email")
    except Exception as e:
        print(e)
        return None


@app.get(
    "/apartments/{apartment_id}", status_code=201, response_model=Apartment,
    summary='По айди получить apartment',
    tags=['apartments']
)
async def get_apartment(
        apartment_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Apartment:
    item = apartment_service.get_apartment(db, apartment_id)
    if item is not None:
        return item
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.get(
    "/apartments",
    summary='Возвращает список apartments',
    response_model=PaginatedApartmentResponse,
    tags=['apartments']
)
async def get_apartments(
        request: Request,
        my_apartments: bool = Query(False, description="Получить свои апартаменты"),
        limit: int = Query(10, description="Максимальное количество записей"),
        offset: int = Query(0, description="Смещение записей"),
        city_name: str = Query(None, description="Название города"),
        radius: float = Query(None, description="радиус в метрах"),
        latitude: float = Query(None, description="широта"),
        longitude: float = Query(None, description="долгота"),
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
) -> PaginatedApartmentResponse:
    """
    Возвращает список ближайших квартир и сортирует по близости.
    В первую очередь по городу.
    Во вторую очередь по широте и долготе.
    Если не указать город и координаты, то вернет просто список квартир.
    """

    if my_apartments:
        apartments = apartment_service.get_my_apartments(db, extract_email_data(request))

        return apartments

    apartments_query = ApartmentsQuery(
        limit=limit,
        offset=offset,
        city_name=city_name,
        radius=radius,
        latitude=latitude,
        longitude=longitude
    )

    apartments = apartment_service.get_apartments(db, apartments_query)

    return PaginatedApartmentResponse(**apartments)


@app.post(
    "/apartments",
    status_code=201,
    response_model=Apartment,
    summary='Добавляет apartment в базу',
    tags=['apartments']
)
async def add_apartment(
        request: Request,
        apartment: BaseApartment,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Apartment:
    p = extract_email_data(request)
    print(p)
    apartment_item_create = ApartmentCreate(**apartment.dict(), publisher_email=p)
    return apartment_service.add_apartment(db, apartment_item_create)


@app.patch(
    "/apartments/{apartment_id}",
    summary='Обновляет информацию об apartment',
    tags=['apartments']
)
async def update_apartment(
        request: Request,
        apartment_id: int,
        updated_item: BaseApartment,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Apartment:
    apartment_item_updated = ApartmentUpdate(**updated_item.dict(), publisher_email=extract_email_data(request))
    item = apartment_service.update_apartment(db, apartment_id, apartment_item_updated)
    if item is not None:
        return item
    return JSONResponse(status_code=404, content={"message": "Item not found"})

@app.delete(
    "/apartments/{apartment_id}",
    summary='Удаляет apartment из базы',
    tags=['apartments']
)
async def delete_apartment(
        apartment_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Apartment:
    if apartment_service.delete_apartment(db, apartment_id):
        return JSONResponse(status_code=200, content={"message": "Item successfully deleted"})
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.get(
    "/favorites",
    summary='Возвращает список favorite items по почте пользователя',
    response_model=PaginatedFavoriteItemsResponse,
    tags=['favorites']
)
async def get_favorite_items(
        request: Request,
        limit: int = 1,
        offset: int = 0,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> typing.List[FavoriteItem]:
    return favorite_service.get_favorite_items_by_user_email(db, user_email=extract_email_data(request), limit=limit, offset=offset)


@app.post(
    "/favorites",
    status_code=201,
    response_model=FavoriteItem,
    summary='Добавляет favorite item в базу',
    tags=['favorites']
)
async def add_favorite_item(
        request: Request,
        favorite_item: BaseFavoriteItem,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> FavoriteItem:
    favorite_item_create = FavoriteItemCreate(**favorite_item.dict(), user_email=extract_email_data(request))
    return favorite_service.add_favorite_item(db, favorite_item_create)

@app.delete(
    "/favorites/{item_id}",
    summary='Удаляет favorite item из базы',
    tags=['favorites']
)
async def delete_favorite_item(
        item_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> FavoriteItem:
    if favorite_service.delete_favorite_item(db, item_id):
        return JSONResponse(status_code=200, content={"message": "Item successfully deleted"})
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.get(
    "/reservations/{reservation_id}", status_code=201, response_model=Reservation,
    summary='По айди получить Reservation',
    tags=['reservations']
)
async def get_reservation(
        reservation_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Reservation:
    item = reservation_service.get_reservation_item(db, reservation_id)
    if item is not None:
        return item
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.get(
    "/reservations",
    summary='Возвращает список reservations',
    response_model=PaginatedReservation,
    tags=['reservations']
)
async def get_reservations(
        request: Request,
        limit: int = 1,
        offset: int = 0,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
) -> typing.List[Reservation]:
    return reservation_service.get_reservation_items(db, extract_email_data(request), limit=limit, offset=offset)


@app.get(
    "/get_reserved_periods_trimmed",
    summary='Возвращает список reservations',
    response_model=List[Tuple[str, datetime.date, datetime.date]],
    tags=['reservations']
)
async def get_reserved_periods_trimmed(
        request: Request,
        apartment_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
) -> List[Tuple[str, datetime.date, datetime.date]]:
    return reservation_service.get_reserved_periods_trimmed(db, apartment_id, start_date, end_date)


@app.get(
    "/get_available_periods",
    summary='Возвращает список reservations',
    response_model=List[Tuple[datetime.date, datetime.date]],
    tags=['reservations']
)
async def get_available_periods(
        request: Request,
        apartment_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
) -> List[Tuple[datetime.date, datetime.date]]:
    return reservation_service.get_available_periods(db, apartment_id, start_date, end_date)


@app.post(
    "/reservations",
    status_code=201,
    response_model=Reservation,
    summary='Добавляет Reservation в базу',
    tags=['reservations']
)
async def add_reservation(
        request: Request,
        reservation: BaseReservation,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Reservation:
    reservation_item_create = ReservationCreate(**reservation.dict(), email=extract_email_data(request))
    item = await reservation_service.add_reservation_item(db, reservation_item_create)
    if item is not None:
        return item
    return JSONResponse(status_code=404, content={"message": f"Элемент уже существует в списке."})


@app.delete(
    "/reservations/{reservation_id}",
    summary='Удаляет favorite item из базы',
    tags=['reservations']
)
async def delete_reservation(
        reservation_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(auth.get_current_active_user())
    ) -> Reservation:
    if reservation_service.delete_reservation_item(db, reservation_id):
        return JSONResponse(status_code=200, content={"message": "Item successfully deleted"})
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.get("/reviews",
         summary="Returns all reviews by apartment_id",
         response_model=List[Review],
         tags=['reviews']
)
async def get_reviews(
    apartment_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(auth.get_current_active_user())
):
    return review_service.get_reviews_by_apartment_id(db, apartment_id, skip, limit)


@app.post("/reviews",
         summary="Add new review",
         response_model=Review,
         tags=['reviews']
)
async def add_review(
    request: Request,
    review: ReviewBase,
    db: Session = Depends(get_db),
    user: User = Depends(auth.get_current_active_user())
) -> Review:
    review_item_create = ReviewCreate(**review.dict(), user_email=extract_email_data(request))
    review = await review_service.add_review(db, review_item_create)
    if review:
        return review
    return JSONResponse(status_code=400, content={"message": "Отзыв уже существует"})

@app.get("/reviews/{review_id}",
         summary="Get review by id",
         tags=['reviews']
)
async def get_review_uid(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(auth.get_current_active_user())
) -> Review:
    review = review_service.get_review_by_uid(db, review_id)
    if review is None:
        return JSONResponse(status_code=404, content={"message": "Not found"})
    return review


@app.patch("/reviews/{review_id}",
         summary="Update review info by id",
         tags=['reviews']
)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(auth.get_current_active_user())
) -> Review:
    review = review_service.update_review_by_uid(db, review_id, review_update)
    if review is None:
        return JSONResponse(status_code=404, content={"message": "Not found"})
    return review


@app.delete("/reviews/{review_id}",
         summary="Delete review by id",
         tags=['reviews']
)
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(auth.get_current_active_user())
) -> Review:
    return review_service.remove_review_by_uid(db, review_id)



@app.post(
    "/groups", status_code=201, response_model=schemas.GroupRead,
    summary='Создает новую группу',
    tags=['groups']
)
async def add_group(
        group: schemas.GroupCreate,
        session: AsyncSession = Depends(async_base.get_async_session)
):
    return await user_service.create_group(group, session)


@app.get(
    "/groups",
    summary='Возвращает список групп',
    response_model=list[schemas.GroupRead],
    tags=['groups']
)
async def get_groups(
        session: AsyncSession = Depends(async_base.get_async_session),
        skip: int = 0,
        limit: int = 100
) -> typing.List[schemas.GroupRead]:
    return await user_service.get_groups(session, skip, limit)


@app.get(
    "/groups/{group_id}",
    summary='Возвращает информацию о группе',
    tags=['groups']
)
async def get_group(
        group_id: int, session: AsyncSession = Depends(async_base.get_async_session)
) -> schemas.GroupRead:
    group = await user_service.get_group(session, group_id)
    if group != None:
        return group
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.put(
    "/groups/{group_id}",
    summary='Обновляет информацию о группе',
    tags=['groups']
)
async def update_group(
        group_id: int,
        group: schemas.GroupUpdate,
        session: AsyncSession = Depends(async_base.get_async_session)
) -> schemas.GroupRead:
    group = await user_service.update_group(session, group_id, group)
    if group != None:
        return group
    return JSONResponse(status_code=404, content={"message": "Item not found"})


@app.delete(
    "/groups/{group_id}",
    summary='Удаляет информацию о группе',
    tags=['groups']
)
async def delete_group(
        group_id: int,
        session: AsyncSession = Depends(async_base.get_async_session)
) -> schemas.GroupRead:
    if await user_service.delete_group(session, group_id):
        return JSONResponse(status_code=200, content={"message": "Item successfully deleted"})
    return JSONResponse(status_code=404, content={"message": "Item not found"})
