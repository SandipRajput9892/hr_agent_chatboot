from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.admin import router as admin_router
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="HR AI Agent",
    description="AI-powered HR assistant for policy Q&A, leave management, and employee queries",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    from app.db.database import engine, Base
    from app.db import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)
    logger.info("HR AI Agent started — model: %s", settings.model_name)
    logger.info("PostgreSQL tables ready")
