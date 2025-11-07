from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core import deps
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def session_maker(tmp_path):
	db_file = tmp_path / "test_post.db"
	engine = create_async_engine(f"sqlite+aiosqlite:///{db_file.as_posix()}", future=True)
	async with engine.begin() as conn:
		await conn.run_sync(SQLModel.metadata.drop_all)
		await conn.run_sync(SQLModel.metadata.create_all)

	session_factory = async_sessionmaker(engine, expire_on_commit=False)

	try:
		yield session_factory
	finally:
		await engine.dispose()


@pytest_asyncio.fixture()
async def test_user() -> SimpleNamespace:
	return SimpleNamespace(id=uuid.uuid7(), is_active=True, is_superuser=False)


@pytest_asyncio.fixture()
async def client(session_maker, test_user):
	async def _override_get_db():
		async with session_maker() as session:
			yield session

	async def _override_current_user():
		return test_user

	app.dependency_overrides[deps.get_db] = _override_get_db
	app.dependency_overrides[deps.current_active_user] = _override_current_user

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as test_client:
		yield test_client

	app.dependency_overrides.pop(deps.get_db, None)
	app.dependency_overrides.pop(deps.current_active_user, None)
