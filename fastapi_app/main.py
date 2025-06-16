# fastapi_app/main.py

import os
import django
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgiref.sync import sync_to_async
from sqlalchemy.ext.asyncio import create_async_engine

# === Setup Django environment ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school.settings")
django.setup()

from quiz.models import School  # Safe to import after Django setup

# === Initialize FastAPI ===
app = FastAPI()

# === Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React/Vue etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Routers ===
from .routers import exam_rules
app.include_router(exam_rules.router)

# === API Endpoints ===

@app.get("/school/")
async def get_schools():
    schools = await sync_to_async(list)(School.objects.all())
    return [{"id": s.id, "school_name": s.school_name} for s in schools]

@app.get("/ping")
async def ping():
    return {"message": "pongrrrrrr1"}

# === Test Async PostgreSQL Connection ===
DATABASE_URL = "postgresql+asyncpg://esteemuser:0806@localhost/esteemcbt"
engine = create_async_engine(DATABASE_URL, echo=True)

@app.on_event("startup")
async def test_db_connection():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: print("✅ Connected to PostgreSQL successfully!"))
    except Exception as e:
        print("❌ Failed to connect to DB:", e)
