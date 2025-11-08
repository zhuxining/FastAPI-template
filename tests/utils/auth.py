from httpx import AsyncClient

from app.core.config import settings


async def get_auth_headers(client: AsyncClient, *, email: str, password: str) -> dict[str, str]:
	response = await client.post(
		f"{settings.API_V1_STR}/auth/jwt/login",
		data={"username": email, "password": password},
	)
	if response.status_code != 200:
		raise AssertionError(
			f"Failed to obtain auth token for {email}: "
			f"status={response.status_code} body={response.text}"
		)
	data = response.json()
	token = data["access_token"]
	return {"Authorization": f"Bearer {token}"}
