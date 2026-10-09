"""Vercel serverless entry for RSA-SHIELD FastAPI."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/rsa_shield.db")
os.environ.setdefault(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,*",
)

from app.main import app  # noqa: E402

# Vercel Python runtime looks for `app` (ASGI)
__all__ = ["app"]
