from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.neo4j import neo4j_driver
from app.api.router import api_router


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fuschia Backend API")
    try:
        await neo4j_driver.verify_connectivity()
        logger.info("Neo4j connection verified")
    except Exception as e:
        logger.warning(f"Neo4j connection failed: {e}")
        logger.info("Starting without Neo4j connection")
    yield
    logger.info("Shutting down Fuschia Backend API")
    await neo4j_driver.close()


app = FastAPI(
    title="Fuschia API",
    description="Intelligent Automation Platform API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    return {"message": "Fuschia Intelligent Automation Platform API"}