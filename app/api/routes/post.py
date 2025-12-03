from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import UUID7, BaseModel, ConfigDict, Field
from sqlmodel import select

from app.core.deps import CurrentUserDep, SessionDep
from app.models import Post, PostCreate, PostRead, PostUpdate
from app.utils.exceptions import ForbiddenException, NotFoundException
from app.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/post", tags=["post"])


@router.post("/", response_model=ResponseEnvelope[PostRead])
async def create_post(
    *,
    db: SessionDep,
    post_in: PostCreate,
    current_user: CurrentUserDep,
):
    post = Post(
        title=post_in.title,
        content=post_in.content,
        is_published=post_in.is_published,
        author_id=current_user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    post_read = PostRead.model_validate(post)
    return success_response(data=post_read, message="创建成功")


class FilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at"] = "created_at"


@router.get("/", response_model=ResponseEnvelope[list[PostRead]])
async def read_posts(
    db: SessionDep,
    filter_query: Annotated[FilterParams, Depends(FilterParams)],
):
    result = await db.execute(select(Post).offset(filter_query.offset).limit(filter_query.limit))
    posts = result.scalars().all()
    post_reads = [PostRead.model_validate(post) for post in posts]
    return success_response(data=post_reads, message="查询成功")


@router.get("/{post_id}", response_model=ResponseEnvelope[PostRead])
async def read_post(
    *,
    db: SessionDep,
    post_id: UUID7,
    current_user: CurrentUserDep,
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException(message="Post not found", error_code="POST_NOT_FOUND")
    post_read = PostRead.model_validate(post)
    return success_response(data=post_read, message="查询成功")


@router.put("/{post_id}", response_model=ResponseEnvelope[PostRead])
async def update_post(
    *,
    db: SessionDep,
    post_id: UUID7,
    post_in: PostUpdate,
    current_user: CurrentUserDep,
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException(message="Post not found", error_code="POST_NOT_FOUND")
    if post.author_id != current_user.id:
        raise ForbiddenException(message="Not enough permissions", error_code="NOT_OWNER")

    post_data = post_in.model_dump(exclude_unset=True)
    for key, value in post_data.items():
        setattr(post, key, value)

    db.add(post)
    await db.commit()
    await db.refresh(post)
    post_read = PostRead.model_validate(post)
    return success_response(data=post_read, message="更新成功")


@router.delete("/{post_id}", response_model=ResponseEnvelope[dict[str, bool]])
async def delete_post(
    *,
    db: SessionDep,
    post_id: UUID7,
    current_user: CurrentUserDep,
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException(message="Post not found", error_code="POST_NOT_FOUND")
    if post.author_id != current_user.id:
        raise ForbiddenException(message="Not enough permissions", error_code="NOT_OWNER")
    await db.delete(post)
    await db.commit()
    return success_response(data={"deleted": True}, message="删除成功")


async def get_post_by_id(post_id: UUID7, db: SessionDep) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundException(message="Post not found", error_code="POST_NOT_FOUND")
    return post
