from typing import Any, TypeVar

from pydantic import BaseModel, Field

from app.utils.logging import get_request_id

DataT = TypeVar("DataT")


class ResponseEnvelope[DataT](BaseModel):
	success: bool = Field(description="请求是否成功")
	data: DataT | None = Field(default=None, description="响应数据")
	error_code: str | None = Field(default=None, description="错误类型编码，用于业务识别")
	message: str | None = Field(default=None, description="展示给用户的提示信息")
	show_type: int | None = Field(
		default=None,
		description="错误展示方式：0 静默；1 message.warn；2 message.error；4 notification；9 page",
	)
	request_id: str | None = Field(default=None, description="请求追踪 ID，定位问题使用")


def _resolve_request_id(request_id: str | None) -> str | None:
	return request_id or get_request_id()


def success_response[DataT](
	data: DataT | None = None,
	message: str | None = None,
	show_type: int | None = None,
	request_id: str | None = None,
) -> ResponseEnvelope[DataT]:
	return ResponseEnvelope[DataT](
		success=True,
		data=data,
		message=message,
		show_type=show_type,
		request_id=_resolve_request_id(request_id),
	)


def error_response(
	error_code: str,
	message: str,
	detail: Any | None = None,
	show_type: int = 2,
	request_id: str | None = None,
) -> ResponseEnvelope[Any]:
	return ResponseEnvelope[Any](
		success=False,
		data=detail,
		error_code=error_code,
		message=message,
		show_type=show_type,
		request_id=_resolve_request_id(request_id),
	)
