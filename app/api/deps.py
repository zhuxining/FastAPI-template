import contextlib
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
	AuthenticationBackend,
	BearerTransport,
	JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserAlreadyExists
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import async_session_maker
from app.models import User, UserCreate


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
	reset_password_token_secret = settings.SECRET_KEY
	verification_token_secret = settings.SECRET_KEY

	async def on_after_register(self, user: User, request: Request | None = None):
		print(f"User {user.id} has registered.")

	async def on_after_forgot_password(
		self, user: User, token: str, request: Request | None = None
	):
		print(f"User {user.id} has forgot their password. Reset token: {token}")

	async def on_after_request_verify(self, user: User, token: str, request: Request | None = None):
		print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_db() -> AsyncGenerator[AsyncSession]:
	async with async_session_maker() as session:
		try:
			yield session
		finally:
			await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_user_db(
	session: SessionDep,
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID]]:
	from app.models.user import (
		OAuthAccount,
		User,
	)  # Import here to avoid circular dependency

	yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


UserDatabaseDep = Annotated[SQLAlchemyUserDatabase[User, uuid.UUID], Depends(get_user_db)]


async def get_user_manager(
	user_db: UserDatabaseDep,
) -> AsyncGenerator[UserManager]:
	yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy:
	return JWTStrategy(
		secret=settings.SECRET_KEY,
		lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
	)


bearer_transport = BearerTransport(tokenUrl=f"{settings.API_V1_STR}/auth/jwt/login")
auth_backend = AuthenticationBackend(
	name="jwt",
	transport=bearer_transport,
	get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

get_async_session_context = contextlib.asynccontextmanager(get_db)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, is_superuser: bool = False):
	try:
		async with (
			get_async_session_context() as session,
			get_user_db_context(session) as user_db,
			get_user_manager_context(user_db) as user_manager,
		):
			user = await user_manager.create(
				UserCreate(email=email, password=password, is_superuser=is_superuser)
			)
			logger.success(f"User created {user}")
			return user
	except UserAlreadyExists:
		logger.warning(f"User {email} already exists")
		pass
