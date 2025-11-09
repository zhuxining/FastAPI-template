import tomllib
from typing import Annotated, Any, Literal, cast

from pydantic import (
	AnyUrl,
	BeforeValidator,
	PostgresDsn,
	computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

with open("pyproject.toml", "rb") as f:
	pyproject = tomllib.load(f)


def parse_cors(v: Any) -> list[str] | str:
	if isinstance(v, str) and not v.startswith("["):
		return [i.strip() for i in v.split(",")]
	elif isinstance(v, list | str):
		return v
	raise ValueError(v)


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		case_sensitive=True,
		extra="allow",  # Allow extra fields from env file
	)

	# General Settings
	ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
	LOG_LEVEL: str = "INFO"  # Logging level
	SWAGGER_UI_ENABLED: bool = True  # Swagger UI, Change in production

	# Database Settings
	DATABASE_TYPE: Literal["postgresql", "sqlite"] = "sqlite"
	SQLITE_URL: str = "sqlite+aiosqlite:///./local.db"
	POSTGRES_SERVER: str = "localhost"
	POSTGRES_PORT: int = 5432
	POSTGRES_DB: str = "app"
	POSTGRES_USER: str = "postgres"
	POSTGRES_PASSWORD: str = "postgres"

	# Security Settings
	BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []  # CORS
	TRUSTED_HOSTS: Annotated[list | str, BeforeValidator(parse_cors)] = []  # Allowed Hosts

	SECRET_KEY: str = "YOUR-SECRET-KEY-123"  # JWT Settings, Change in production
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

	FIRST_SUPERUSER_EMAIL: str = "admin@admin.com"  # First Superuser
	FIRST_SUPERUSER_PASSWORD: str = "admin@admin.com"

	# OpenAPI Docs Settings, loaded from pyproject.toml
	API_V1_STR: str = "/api/v1"
	PROJECT_NAME: str = pyproject.get("project", {}).get("name")
	VERSION: str = pyproject.get("project", {}).get("version")
	DESCRIPTION: str = pyproject.get("project", {}).get("description")

	@computed_field
	@property
	def all_cors_origins(self) -> list[str]:
		return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

	@computed_field
	@property
	def postgre_url(self) -> PostgresDsn:
		url = MultiHostUrl.build(
			scheme="postgresql+asyncpg",
			username=self.POSTGRES_USER,
			password=self.POSTGRES_PASSWORD,
			host=self.POSTGRES_SERVER,
			port=self.POSTGRES_PORT,
			path=self.POSTGRES_DB,
		)
		return cast(PostgresDsn, str(url))


settings = Settings()
