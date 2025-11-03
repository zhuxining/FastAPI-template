from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID7, BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app import models
from app.api import deps
from app.models import Post, User

SessionDep = Annotated[AsyncSession, Depends(deps.get_db)]
CurrentUserDep = Annotated[User, Depends(deps.current_active_user)]

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=models.PostRead)
async def create_post(
	*,
	db: SessionDep,
	post_in: models.PostCreate,
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
	return post


class FilterParams(BaseModel):
	model_config = ConfigDict(extra="forbid")

	limit: int = Field(100, gt=0, le=100)
	offset: int = Field(0, ge=0)
	order_by: Literal["created_at"] = "created_at"


@router.get("/", response_model=list[models.PostRead])
async def read_posts(
	db: SessionDep,
	filter_query: Annotated[FilterParams, Depends(FilterParams)],
):
	result = await db.execute(select(Post).offset(filter_query.offset).limit(filter_query.limit))
	posts = result.scalars().all()
	return posts


@router.get("/{post_id}", response_model=models.PostRead)
async def read_post(
	*,
	db: SessionDep,
	post_id: UUID7,
	current_user: CurrentUserDep,
):
	result = await db.execute(select(Post).where(Post.id == post_id))
	post = result.scalar_one_or_none()
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")
	return post


@router.put("/{post_id}", response_model=models.PostUpdate)
async def update_post(
	*,
	db: SessionDep,
	post_id: UUID7,
	post_in: models.PostUpdate,
	current_user: CurrentUserDep,
):
	result = await db.execute(select(Post).where(Post.id == post_id))
	post = result.scalar_one_or_none()
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")
	if post.author_id != current_user.id:
		raise HTTPException(status_code=403, detail="Not enough permissions")

	post_data = post_in.model_dump(exclude_unset=True)
	for key, value in post_data.items():
		setattr(post, key, value)

	db.add(post)
	await db.commit()
	await db.refresh(post)
	return post


@router.delete("/{post_id}")
async def delete_post(
	*,
	db: SessionDep,
	post_id: UUID7,
	current_user: CurrentUserDep,
):
	result = await db.execute(select(Post).where(Post.id == post_id))
	post = result.scalar_one_or_none()
	if not post:
		raise HTTPException(status_code=404, detail="Post not found")
	if post.author_id != current_user.id:
		raise HTTPException(status_code=403, detail="Not enough permissions")
	await db.delete(post)
	await db.commit()
	return {"ok": True}
