from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import CreateSchema

from typing import AsyncGenerator


class Database_Initializer():
    def __init__(self, base, schema):
        self.base = base
        self.schema = schema
        self.async_session_maker = None

    async def init_db(self, postgre_dsn):
        engine = create_async_engine(postgre_dsn)
        self.async_session_maker = async_sessionmaker(
            engine, expire_on_commit=False
        )
        async with engine.begin() as connection:
            # create schema
            schema = self.schema

            def check_schema(conn):
                return inspect(conn).has_schema(schema)

            if not (await connection.run_sync(check_schema)):
                await connection.execute(CreateSchema(schema))
                # await connection.commit()

            # create metadata
            await connection.run_sync(self.base.metadata.create_all)


SCHEMA = "users"
BASE = declarative_base()
DB_INITIALIZER = Database_Initializer(BASE, SCHEMA)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with DB_INITIALIZER.async_session_maker() as session:
        yield session