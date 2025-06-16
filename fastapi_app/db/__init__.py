# fastapi_app/db/__init__.py
from .session import AsyncSessionLocal

async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
