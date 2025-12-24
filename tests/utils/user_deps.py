from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar
import uuid

from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import UserManager
from app.models.user import OAuthAccount, User, UserCreate

from .data import random_email, random_lower_string

T = TypeVar("T")


@dataclass(slots=True)
class CreatedUser:
    instance: User
    password: str

    @property
    def id(self) -> uuid.UUID:
        if not self.instance.id:
            raise ValueError("User id is not set")
        return self.instance.id


class UserFactory:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self._session_maker = session_maker

    async def _with_session(
        self,
        fn: Callable[[AsyncSession], Awaitable[T]],
        session: AsyncSession | None = None,
    ) -> T:
        if session is not None:
            return await fn(session)
        async with self._session_maker() as managed_session:
            return await fn(managed_session)

    async def create(
        self,
        *,
        email: str | None = None,
        password: str | None = None,
        is_active: bool = True,
        is_superuser: bool = False,
        is_verified: bool = True,
        session: AsyncSession | None = None,
    ) -> CreatedUser:
        email = email or random_email()
        password = password or random_lower_string()

        async def _create(target_session: AsyncSession) -> CreatedUser:
            user_db = SQLAlchemyUserDatabase(target_session, User, OAuthAccount)
            user_manager = UserManager(user_db)
            user = await user_manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_active=is_active,
                    is_superuser=is_superuser,
                    is_verified=is_verified,
                )
            )
            await target_session.commit()
            await target_session.refresh(user)
            return CreatedUser(instance=user, password=password)

        result = await self._with_session(_create, session=session)
        assert result is not None
        return result

    async def create_active(
        self,
        *,
        session: AsyncSession | None = None,
        **kwargs,
    ) -> CreatedUser:
        return await self.create(is_active=True, session=session, **kwargs)

    async def create_superuser(
        self,
        *,
        session: AsyncSession | None = None,
        **kwargs,
    ) -> CreatedUser:
        return await self.create(is_superuser=True, session=session, **kwargs)
