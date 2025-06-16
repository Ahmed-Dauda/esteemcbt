from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends
from dotenv import load_dotenv
load_dotenv()

import os

DATABASE_URL = os.getenv("FASTAPI_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment!")


# DATABASE_URL = "postgresql+asyncpg://esteemuser:0806@localhost/esteemcbt"


# Async Engine
async_engine = create_async_engine(DATABASE_URL, echo=True)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base model
Base = declarative_base()

# Dependency to get async session
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
