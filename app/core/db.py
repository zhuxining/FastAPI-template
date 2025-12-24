from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings
from app.models.user import Base

IS_POSTGRESQL = settings.DATABASE_TYPE == "postgresql"

database_url = (
    settings.postgre_url if IS_POSTGRESQL else f"sqlite+aiosqlite:///{settings.SQLITE_URL}"
)

# Create engine with schema options for PostgreSQL
engine_kwargs = {"echo": False, "future": True}
if IS_POSTGRESQL:
    engine_kwargs["connect_args"] = {"server_settings": {"search_path": settings.POSTGRES_SCHEMA}}

engine = create_async_engine(str(database_url), **engine_kwargs)


# Set schema for all PostgreSQL connections
def _setup_postgresql_schema():
    """Setup PostgreSQL schema creation and search_path configuration."""

    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        try:
            schema_name = settings.POSTGRES_SCHEMA
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
            cursor.execute(f"SET search_path TO {schema_name};")
        finally:
            cursor.close()


if IS_POSTGRESQL:
    _setup_postgresql_schema()

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(SQLModel.metadata.create_all)
