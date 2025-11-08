from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from fastapi_users.db import SQLAlchemyUserDatabase
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import UserManager
from app.models import Post
from app.models.user import OAuthAccount, User, UserCreate
from tests.utils.auth import get_auth_headers
from tests.utils.data import random_email, random_lower_string

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


@dataclass(slots=True)
class _BaseFactory:
	_session_maker: async_sessionmaker[AsyncSession]

	async def _with_session(
		self,
		fn: Callable[[AsyncSession], Awaitable[T]],
		session: AsyncSession | None = None,
	) -> T:
		if session is not None:
			return await fn(session)
		async with self._session_maker() as managed_session:
			return await fn(managed_session)


class UserFactory(_BaseFactory):
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

		return await self._with_session(_create, session=session)

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

	async def create_with_token(
		self,
		client: AsyncClient,
		*,
		session: AsyncSession | None = None,
		**kwargs,
	) -> tuple[CreatedUser, dict[str, str]]:
		created_user = await self.create(session=session, **kwargs)
		headers = await get_auth_headers(
			client,
			email=created_user.instance.email,
			password=created_user.password,
		)
		return created_user, headers


class PostFactory(_BaseFactory):
	def __init__(self, session_maker: async_sessionmaker[AsyncSession], user_factory: UserFactory):
		super().__init__(session_maker)
		self._user_factory = user_factory

	async def create(
		self,
		*,
		title: str | None = None,
		content: str | None = None,
		is_published: bool = True,
		author_id: uuid.UUID | None = None,
		author: User | None = None,
		session: AsyncSession | None = None,
	) -> Post:
		title = title or f"post-{random_lower_string(6)}"
		content = content or random_lower_string(24)

		async def _create(target_session: AsyncSession) -> Post:
			target_author_id = author_id or (author.id if author else None)
			if target_author_id is None:
				created_author = await self._user_factory.create(session=target_session)
				target_author_id = created_author.id

			post = Post(
				title=title,
				content=content,
				is_published=is_published,
				author_id=target_author_id,
			)
			target_session.add(post)
			await target_session.commit()
			await target_session.refresh(post)
			return post

		return await self._with_session(_create, session=session)
