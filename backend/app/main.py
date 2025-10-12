from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.db.neo4j import neo4j_driver
from app.db.postgres import init_db, test_db_connection
from app.api.router import api_router

# Reduce uvicorn access log verbosity
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

print("Starting Fuschia Backend API...")
logger = structlog.get_logger()
print("Logger initialized")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Fuschia Backend API")
    
    # Initialize PostgreSQL database
    try:
        logger.info("Initializing PostgreSQL database...")
        await init_db()
        logger.info("PostgreSQL database initialized successfully")
        
        # Test connection
        pg_connected = await test_db_connection()
        if pg_connected:
            logger.info("PostgreSQL connection verified")
        else:
            logger.warning("PostgreSQL connection test failed")
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")
        logger.info("Starting without PostgreSQL connection")
    
    # Initialize Neo4j database
    try:
        await neo4j_driver.verify_connectivity()
        logger.info("Neo4j connection verified")
    except Exception as e:
        logger.warning(f"Neo4j connection failed: {e}")
        logger.info("Starting without Neo4j connection")
    
    # Initialize WebSocket manager message processing
    try:
        from app.services.websocket_manager import initialize_websocket_manager
        await initialize_websocket_manager()
        logger.info("WebSocket manager message processing initialized")
    except Exception as e:
        logger.error(f"WebSocket manager initialization failed: {e}")

    # Initialize Gmail Monitor Service (optional auto-start)
    try:
        from app.services.gmail_monitor_service import gmail_monitor_service
        logger.info("Gmail Monitor Service available - use /api/v1/gmail-monitor/start to enable")
        # Uncomment the following lines to auto-start monitoring on application startup:
        await gmail_monitor_service.initialize()
        await gmail_monitor_service.start_monitoring()
        logger.info("Gmail Monitor Service started automatically")
    except Exception as e:
        logger.warning(f"Gmail Monitor Service initialization failed: {e}")

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