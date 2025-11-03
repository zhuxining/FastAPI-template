import uuid

from fastapi_users import schemas
from fastapi_users.db import (
	SQLAlchemyBaseOAuthAccountTableUUID,
	SQLAlchemyBaseUserTableUUID,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


class Base(DeclarativeBase):
	pass


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
	pass


class User(SQLAlchemyBaseUserTableUUID, Base):
	oauth_accounts: Mapped[list[OAuthAccount]] = relationship("OAuthAccount", lazy="joined")


# pydantic models


class UserRead(schemas.BaseUser[uuid.UUID]):
	pass


class UserCreate(schemas.BaseUserCreate):
	pass


class UserUpdate(schemas.BaseUserUpdate):
	pass
