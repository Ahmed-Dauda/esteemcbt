# fastapi_app/fastapi_asgi.py
from fastapi import FastAPI
from fastapi_app.routers import exam_rules  # or your actual routers

app = FastAPI(
    title="Esteem CBT API",
    docs_url="/docs",  # optional
    redoc_url="/redoc",  # optional
)

# Include routers
app.include_router(exam_rules.router)
