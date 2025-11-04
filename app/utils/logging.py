import logging
import sys
import uuid
from contextvars import ContextVar
from time import perf_counter

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")
_LOGGING_INITIALIZED = False


class InterceptHandler(logging.Handler):
	def emit(self, record: logging.LogRecord):
		try:
			level = logger.level(record.levelname).name
		except ValueError:
			level = record.levelno
		logger.bind(request_id=request_id_ctx_var.get()).opt(
			depth=6, exception=record.exc_info, colors=True
		).log(level, record.getMessage())


class RequestLoggingMiddleware(BaseHTTPMiddleware):
	def __init__(self, app: ASGIApp):
		super().__init__(app)

	async def dispatch(self, request: Request, call_next):
		request_id = uuid.uuid4().hex
		token = request_id_ctx_var.set(request_id)
		request.state.request_id = request_id

		client = request.client.host if request.client else "-"
		logger.bind(request_id=request_id).info(
			"Received request | method={} path={} client={}",
			request.method,
			request.url.path,
			client,
		)
		start_time = perf_counter()

		try:
			response = await call_next(request)
		except Exception:
			logger.bind(request_id=request_id).exception("Unhandled exception during request")
			raise
		else:
			process_time = perf_counter() - start_time
			logger.bind(request_id=request_id).info(
				"Handled request | status={} duration={:.3f}s",
				response.status_code,
				process_time,
			)
			response.headers["X-Request-ID"] = request_id
			response.headers["X-Process-Time"] = f"{process_time:.3f}"
			return response
		finally:
			request_id_ctx_var.reset(token)


def setup_logging(settings, *, force: bool = False):
	global _LOGGING_INITIALIZED
	if _LOGGING_INITIALIZED and not force:
		return

	log_level = getattr(settings, "LOG_LEVEL", "INFO")

	logger.remove()
	logger.configure(extra={"request_id": "-"})

	log_format = (
		"<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
		"<level>{level:<8}</level> | "
		"rid={extra[request_id]} | "
		"{name}:{line} - {message}"
	)

	logger.add(
		sys.stdout,
		level=log_level,
		format=log_format,
		colorize=True,
		backtrace=settings.ENVIRONMENT == "dev",
		diagnose=settings.ENVIRONMENT == "dev",
		enqueue=True,
	)
	logger.add(
		"logs/app_{time:YYYY-MM-DD}.log",
		level=log_level,
		format=log_format,
		rotation="1 day",
		retention="14 days",
		enqueue=True,
	)

	logging.basicConfig(handlers=[InterceptHandler()], level=logging.NOTSET, force=True)

	for noisy_logger in ("uvicorn", "uvicorn.access", "sqlalchemy"):
		existing_logger = logging.getLogger(noisy_logger)
		existing_logger.handlers = [InterceptHandler()]
		existing_logger.propagate = False

	_LOGGING_INITIALIZED = True


def get_request_id() -> str | None:
	request_id = request_id_ctx_var.get()
	if request_id == "-":
		return None
	return request_id
