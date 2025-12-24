from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.responses import error_response


class AppException(Exception):
    status_code: int = 400
    error_code: str = "APP_ERROR"
    message: str = "应用异常"
    detail: Any | None = None
    headers: dict[str, str] | None = None
    show_type: int = 2

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        detail: Any | None = None,
        headers: dict[str, str] | None = None,
        show_type: int | None = None,
    ):
        if message is not None:
            self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        if detail is not None:
            self.detail = detail
        self.headers = headers
        if show_type is not None:
            self.show_type = show_type

        super().__init__(self.message)


class NotFoundException(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "资源不存在"


class ForbiddenException(AppException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "无权限执行该操作"


class ConflictException(AppException):
    status_code = 409
    error_code = "CONFLICT"
    message = "资源冲突"


async def _build_json_response(
    request: Request,
    *,
    status_code: int,
    error_code: str,
    message: str,
    detail: Any | None = None,
    show_type: int = 2,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body = error_response(
        error_code=error_code,
        message=message,
        detail=detail,
        show_type=show_type,
        request_id=request_id,
    ).model_dump()
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.bind(request_id=getattr(request.state, "request_id", None)).warning(
            "AppException raised | code={} message={} detail={}",
            exc.error_code,
            exc.message,
            exc.detail,
        )
        return await _build_json_response(
            request,
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            detail=exc.detail,
            show_type=exc.show_type,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.bind(request_id=getattr(request.state, "request_id", None)).warning(
            "HTTPException raised | status={} detail={}", exc.status_code, exc.detail
        )
        return await _build_json_response(
            request,
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            detail=exc.detail,
            show_type=2,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.bind(request_id=getattr(request.state, "request_id", None)).warning(
            "Request validation error | errors={}", exc.errors()
        )
        return await _build_json_response(
            request,
            status_code=422,
            error_code="VALIDATION_ERROR",
            message="请求参数校验失败",
            detail=exc.errors(),
            show_type=1,
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        logger.bind(request_id=getattr(request.state, "request_id", None)).warning(
            "Validation error | errors={}", exc.errors()
        )
        return await _build_json_response(
            request,
            status_code=400,
            error_code="VALIDATION_ERROR",
            message="数据校验失败",
            detail=exc.errors(),
            show_type=1,
        )
