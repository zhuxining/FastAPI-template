from typing import Annotated, Generic, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationQuery(BaseModel):
    """通用分页查询参数"""

    model_config = ConfigDict(extra="forbid")

    current: int = Query(1, ge=1, description="页码")
    page_size: int = Query(10, ge=1, le=100, description="每页数量")
    order_by: str = Query("created_at", description="排序字段")
    desc: bool = Query(True, description="是否倒序")

    @property
    def offset(self) -> int:
        return (self.current - 1) * self.page_size


class PaginatedResponse[T](BaseModel):
    """通用分页响应模型"""

    items: list[T]
    total: int
    current: int
    page_size: int


PaginationDep = Annotated[PaginationQuery, Depends()]
