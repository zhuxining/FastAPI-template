import contextlib

from fastapi_users.exceptions import UserAlreadyExists
from loguru import logger

from app.core.deps import get_db_session, get_user_db_session, get_user_manager
from app.models import UserCreate

get_db_session_context = contextlib.asynccontextmanager(get_db_session)
get_user_db_session_context = contextlib.asynccontextmanager(get_user_db_session)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, is_superuser: bool = False):
    try:
        async with (
            get_db_session_context() as session,
            get_user_db_session_context(session) as user_db,
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
