from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core import deps
from app.main import app
from app.models.user import Base as UserBase
from tests.utils.factories import CreatedUser, PostFactory, UserFactory


@pytest_asyncio.fixture(scope="session", autouse=True)
async def session_maker(tmp_path_factory):
	tmp_dir = tmp_path_factory.mktemp("db")
	db_file = tmp_dir / "test_post.db"
	engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.as_posix()}", future=True)
	async with engine.begin() as conn:
		await conn.run_sync(UserBase.metadata.drop_all)
		await conn.run_sync(SQLModel.metadata.drop_all)
		await conn.run_sync(UserBase.metadata.create_all)
		await conn.run_sync(SQLModel.metadata.create_all)

	session_factory = async_sessionmaker(engine, expire_on_commit=False)

	try:
		yield session_factory
	finally:
		await engine.dispose()


@pytest.fixture(scope="session")
def user_factory(session_maker) -> UserFactory:
	return UserFactory(session_maker)


@pytest.fixture(scope="session")
def post_factory(session_maker, user_factory: UserFactory) -> PostFactory:
	return PostFactory(session_maker, user_factory)


@pytest_asyncio.fixture()
async def db_session(session_maker):
	async with session_maker() as session:
		try:
			yield session
		finally:
			await session.rollback()


@pytest_asyncio.fixture()
async def test_user(user_factory: UserFactory) -> CreatedUser:
	return await user_factory.create_active()


@pytest_asyncio.fixture()
async def client(session_maker, test_user: CreatedUser):
	async def _override_get_db():
		async with session_maker() as session:
			yield session

	async def _override_current_user():
		return test_user.instance

	app.dependency_overrides[deps.get_db] = _override_get_db
	app.dependency_overrides[deps.current_active_user] = _override_current_user

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as test_client:
		yield test_client

	app.dependency_overrides.pop(deps.get_db, None)
	app.dependency_overrides.pop(deps.current_active_user, None)
