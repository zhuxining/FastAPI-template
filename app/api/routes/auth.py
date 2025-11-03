from fastapi import APIRouter

from app.api.deps import auth_backend, fastapi_users
from app.models import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

# Authentication routes
router.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/jwt")

router.include_router(
	fastapi_users.get_register_router(UserRead, UserCreate),
)

router.include_router(
	fastapi_users.get_reset_password_router(),
)

router.include_router(
	fastapi_users.get_verify_router(UserRead),
)
