from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.database.session import init_db
from app.services.audit_service import ensure_demo_user
from app.database.session import SessionLocal

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with SessionLocal() as db:
        await ensure_demo_user(db)
    yield


app = FastAPI(
    title="RSA-SHIELD API",
    description="RSA Key Security Auditor for Legacy Critical Infrastructure — Team Aegis, Bennett University",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "product": "RSA-SHIELD",
        "message": "Mathematical Assurance for RSA Key Security",
        "docs": "/docs",
        "api": settings.api_prefix,
    }
