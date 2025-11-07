from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core.config import settings
from app.models import Post


@pytest.mark.asyncio()
async def test_create_post_success(
	client: AsyncClient,
	session_maker,
	test_user: SimpleNamespace,
):
	payload = {"title": "测试 Post", "content": "测试内容", "is_published": True}

	response = await client.post(f"{settings.API_V1_STR}/post/", json=payload)

	assert response.status_code == 200
	body = response.json()
	assert body["success"] is True
	assert body["message"] == "创建成功"
	assert body["data"]["title"] == payload["title"]

	async with session_maker() as session:
		result = await session.execute(select(Post))
		posts = result.scalars().all()

		assert len(posts) == 1
		saved_post = posts[0]
		assert saved_post.title == payload["title"]
		assert saved_post.author_id == test_user.id
