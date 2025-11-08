from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.config import settings
from app.models import Post
from tests.utils.user_deps import CreatedUser


def test_create_post_success(
	client: TestClient,
	session_maker,
	test_user: CreatedUser,
):
	payload = {"title": "测试 Post", "content": "测试内容", "is_published": True}

	response = client.post(f"{settings.API_V1_STR}/post/", json=payload)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "创建成功"
	assert body["data"]["title"] == payload["title"]

	async def _fetch_posts():
		async with session_maker() as session:
			result = await session.execute(select(Post))
			posts = result.scalars().all()
			return posts

	posts = asyncio.run(_fetch_posts())
	assert len(posts) == 1
	saved_post = posts[0]
	assert saved_post.title == payload["title"]
	assert saved_post.author_id == test_user.id
