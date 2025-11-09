from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
from app.models.user import Base

database_url = (
	settings.postgre_url if settings.DATABASE_TYPE == "postgresql" else settings.SQLITE_URL
)

engine = create_async_engine(str(database_url), echo=False, future=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_tables():
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
		await conn.run_sync(SQLModel.metadata.create_all)
