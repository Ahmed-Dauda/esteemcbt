import asyncio
from fastapi_app.db.base import Base
from fastapi_app.db.session import engine

from fastapi_app.models.exam_rules import ExamsRules  # Make sure the model is imported

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
