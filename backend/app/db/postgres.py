from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, text, Integer, JSON, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv
import structlog
from app.models.user import UserRole
from app.models.template import TemplateType, TemplateComplexity, TemplateStatus

load_dotenv()

logger = structlog.get_logger()

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///./fuschia_users.db"
)

# Create async engine with appropriate settings for different databases
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,  # Set to False in production
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,  # Set to False in production
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for all models
class Base(DeclarativeBase):
    pass

# User table model
class UserTable(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="end_user")  # Use String instead of Enum for SQLite compatibility
    is_active = Column(Boolean, default=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Simplified for SQLite
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Template table model
class TemplateTable(Base):
    __tablename__ = "templates"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    template_type = Column(String, nullable=False, index=True)  # 'workflow' or 'agent'
    complexity = Column(String, nullable=False, default="medium")  # 'simple', 'medium', 'advanced'
    estimated_time = Column(String(50), nullable=False)
    tags = Column(JSON, nullable=False, default=list)  # List of tags as JSON
    preview_steps = Column(JSON, nullable=False, default=list)  # List of preview steps as JSON
    usage_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="active")  # 'active', 'inactive', 'draft', 'archived'
    template_data = Column(JSON, nullable=False, default=dict)  # Nodes/edges data as JSON
    template_metadata = Column(JSON, nullable=True, default=dict)  # Additional metadata as JSON
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database dependency  
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()

# Alternative database session for direct usage
async def get_db_session() -> AsyncSession:
    """Get database session for direct usage"""
    return AsyncSessionLocal()

# Initialize database
async def init_db():
    """Create database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

# Test database connection
async def test_db_connection():
    """Test database connectivity"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False