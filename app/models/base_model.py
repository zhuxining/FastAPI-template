import uuid
from datetime import datetime

from sqlmodel import Column, DateTime, Field, SQLModel, func


class BaseModel(SQLModel):
	__abstract__ = True

	id: uuid.UUID = Field(
		default_factory=uuid.uuid7,
		primary_key=True,
		sa_column_kwargs={"comment": "主键ID, UUID v7"},
	)
	created_at: datetime | None = Field(
		default=None,
		sa_column=Column(
			DateTime(timezone=True),
			server_default=func.current_timestamp(),
			comment="创建时间, timestamptz",
		),
	)
	updated_at: datetime | None = Field(
		default=None,
		sa_column=Column(
			DateTime(timezone=True),
			onupdate=func.current_timestamp(),
			comment="更新时间, timestamptz",
		),
	)
	is_deleted: bool = Field(
		default=False,
		sa_column_kwargs={"comment": "是否软删除"},
	)
	deleted_at: datetime | None = Field(
		default=None,
		sa_column=Column(DateTime(timezone=True), comment="删除时间, timestamptz"),
	)
