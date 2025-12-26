from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastcrud import FastCRUD
from pydantic import UUID7

from app.core.deps import CurrentUserDep, SessionDep
from app.models import Post, PostCreate, PostRead, PostUpdate
from app.utils.exceptions import ForbiddenException, NotFoundException
from app.utils.pagination import PaginatedResponse, PaginationQuery
from app.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/posts", tags=["posts"])

posts_crud = FastCRUD(Post)


class PostPaginationQuery(PaginationQuery):
    order_by: Literal[
        "id", "title", "content", "is_published", "author_id", "created_at", "updated_at"
    ] = Query("created_at", description="排序字段")


PostPaginationDep = Annotated[PostPaginationQuery, Depends()]


async def get_post_or_404(db: SessionDep, post_id: UUID7) -> Post:
    """获取文章或抛出404异常"""
    post = await posts_crud.get(db, id=post_id, schema_to_select=Post, return_as_model=True)
    if not post:
        raise NotFoundException(message="文章不存在", error_code="POST_NOT_FOUND")
    return post


def check_post_owner(post: Post, user_id: UUID7) -> None:
    """检查文章所有权"""
    if post.author_id != user_id:
        raise ForbiddenException(message="无权操作此文章", error_code="PERMISSION_DENIED")


@router.post("/", response_model=ResponseEnvelope[PostRead], summary="创建文章")
async def create_post(
    *,
    db: SessionDep,
    post_in: PostCreate,
    current_user: CurrentUserDep,
):
    """
    创建新文章
    """
    # 构造包含 author_id 的数据
    post_data = post_in.model_dump()
    post_data["author_id"] = current_user.id
    post_input = Post(**post_data)

    post = await posts_crud.create(
        db, object=post_input, schema_to_select=Post, return_as_model=True
    )
    return success_response(data=PostRead.model_validate(post), message="创建成功")


@router.get(
    "/", response_model=ResponseEnvelope[PaginatedResponse[PostRead]], summary="获取文章列表"
)
async def list_posts(
    db: SessionDep,
    pagination: PostPaginationDep,
):
    """
    分页获取文章列表
    """
    posts_data = await posts_crud.get_multi(
        db,
        offset=pagination.offset,
        limit=pagination.page_size,
        sort_columns=[pagination.order_by],
        sort_orders=["desc" if pagination.desc else "asc"],
        return_total_count=True,
        schema_to_select=Post,
        return_as_model=True,
    )

    return success_response(
        data=PaginatedResponse(
            items=[PostRead.model_validate(p) for p in posts_data["data"]],
            total=posts_data["total_count"],
            current=pagination.current,
            page_size=pagination.page_size,
        ),
        message="查询成功",
    )


@router.get(
    "/me", response_model=ResponseEnvelope[PaginatedResponse[PostRead]], summary="获取我的文章列表"
)
async def list_my_posts(
    db: SessionDep,
    pagination: PostPaginationDep,
    current_user: CurrentUserDep,
):
    """
    分页获取当前用户的文章列表
    """
    posts_data = await posts_crud.get_multi(
        db,
        offset=pagination.offset,
        limit=pagination.page_size,
        sort_columns=[pagination.order_by],
        sort_orders=["desc" if pagination.desc else "asc"],
        return_total_count=True,
        schema_to_select=Post,
        return_as_model=True,
        author_id=current_user.id,
    )

    return success_response(
        data=PaginatedResponse(
            items=[PostRead.model_validate(p) for p in posts_data["data"]],
            total=posts_data["total_count"],
            current=pagination.current,
            page_size=pagination.page_size,
        ),
        message="查询成功",
    )


@router.get("/{post_id}", response_model=ResponseEnvelope[PostRead], summary="获取文章详情")
async def get_post(
    post_id: UUID7,
    db: SessionDep,
    # current_user: CurrentUserDep, # 如果是公开接口, 可以去掉 current_user
):
    """
    根据ID获取文章详情
    """
    post = await get_post_or_404(db, post_id)
    return success_response(data=PostRead.model_validate(post), message="查询成功")


@router.patch("/{post_id}", response_model=ResponseEnvelope[PostRead], summary="更新文章")
async def update_post(
    *,
    db: SessionDep,
    post_id: UUID7,
    post_in: PostUpdate,
    current_user: CurrentUserDep,
):
    """
    更新文章(部分更新)
    """
    post = await get_post_or_404(db, post_id)
    check_post_owner(post, current_user.id)

    # 使用 fastcrud 更新
    updated_post = await posts_crud.update(
        db, object=post_in, id=post_id, schema_to_select=Post, return_as_model=True
    )
    return success_response(data=PostRead.model_validate(updated_post), message="更新成功")


@router.delete("/{post_id}", response_model=ResponseEnvelope[dict[str, bool]], summary="删除文章")
async def delete_post(
    *,
    db: SessionDep,
    post_id: UUID7,
    current_user: CurrentUserDep,
):
    """
    删除文章
    """
    post = await get_post_or_404(db, post_id)
    check_post_owner(post, current_user.id)

    await posts_crud.delete(db, id=post_id)
    return success_response(data={"deleted": True}, message="删除成功")
