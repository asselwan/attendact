import os
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import audit, geocode, outcomes, score


@asynccontextmanager
async def lifespan(app: FastAPI):
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)
    yield


app = FastAPI(
    title="Noshight API",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,https://noshight.nomoi.ai").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(score.router, prefix="/api/score", tags=["scoring"])
app.include_router(geocode.router, prefix="/api", tags=["location"])
app.include_router(outcomes.router, prefix="/api/outcomes", tags=["outcomes"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "product": "noshight"}


# Serve React static build in production (built into /app/static by Dockerfile)
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
