from fastapi import APIRouter

from app.api.routes import auth, post, user

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(post.router)
