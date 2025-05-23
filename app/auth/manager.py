import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from app.database import models
from app import config
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
# from fastapi_users.db import BeanieUserDatabase, ObjectIDIDMixin

from app.database.models import User


class UserManager(UUIDIDMixin, BaseUserManager[models.User, uuid.UUID]):

    async def on_after_register(self, user: models.User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
            self, user: models.User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
            self, user: models.User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(
        user_db=Depends(models.get_user_db),
):
    user_manager = UserManager(user_db)
    user_manager.reset_password_token_secret = config.load_config().reset_password_token_secret
    user_manager.verification_token_secret = config.load_config().verification_token_secret
    yield user_manager

