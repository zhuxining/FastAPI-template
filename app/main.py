from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.routing import APIRoute
from loguru import logger

from app.api import api_router
from app.core.config import settings
from app.core.db import create_db_and_tables
from app.core.deps import create_user
from app.utils.exceptions import register_exception_handlers
from app.utils.logging import RequestLoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
	setup_logging(settings)
	logger.info("FastAPI app startup")
	await create_db_and_tables()
	await create_user(settings.FIRST_SUPERUSER_EMAIL, settings.FIRST_SUPERUSER_PASSWORD)
	logger.success("Startup initialization complete")
	try:
		yield
	finally:
		logger.info("FastAPI app shutdown")


def custom_generate_unique_id(route: APIRoute):
	return f"{route.tags[0]}-{route.name}"


app = FastAPI(
	title=settings.PROJECT_NAME,
	description=settings.DESCRIPTION,
	openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.SWAGGER_UI_ENABLED else None,
	docs_url="/docs" if settings.SWAGGER_UI_ENABLED else None,
	redoc_url="/redoc" if settings.SWAGGER_UI_ENABLED else None,
	version=settings.VERSION,
	lifespan=lifespan,
	generate_unique_id_function=custom_generate_unique_id,
	debug=(settings.ENVIRONMENT == "dev"),
)
register_exception_handlers(app)

# CORS middleware
if settings.all_cors_origins:
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.all_cors_origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

if settings.ENVIRONMENT == "prod":
	app.add_middleware(HTTPSRedirectMiddleware)
	app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)
