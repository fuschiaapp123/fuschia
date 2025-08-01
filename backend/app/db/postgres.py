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


# Workflow Template table model (workflow templates only)
class WorkflowTemplateTable(Base):
    __tablename__ = "workflow_templates"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    complexity = Column(String, nullable=False, default="medium")  # 'simple', 'medium', 'advanced'
    estimated_time = Column(String(50), nullable=False)
    tags = Column(JSON, nullable=False, default=list)  # List of tags as JSON
    preview_steps = Column(JSON, nullable=False, default=list)  # List of preview steps as JSON
    usage_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="active")  # 'active', 'inactive', 'draft', 'archived'
    template_data = Column(JSON, nullable=False, default=dict)  # Workflow nodes/edges data as JSON
    template_metadata = Column(JSON, nullable=True, default=dict)  # Additional metadata as JSON
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Legacy template table for backward compatibility (can be removed after migration)
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


# Agent Template table model (serves as both agent templates and instances)
class AgentTemplateTable(Base):
    __tablename__ = "agent_templates"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=False)
    
    # Template characteristics
    category = Column(String(100), nullable=False, index=True)
    complexity = Column(String, nullable=False, default="medium")  # 'simple', 'medium', 'advanced'
    estimated_time = Column(String(50), nullable=False)
    tags = Column(JSON, nullable=False, default=list)  # List of tags as JSON
    preview_steps = Column(JSON, nullable=False, default=list)  # List of preview steps as JSON
    
    # Template vs Instance differentiation
    is_template = Column(Boolean, nullable=False, default=True)  # True for templates, False for instances
    template_id = Column(String, ForeignKey("agent_templates.id"), nullable=True, index=True)  # Points to template if this is an instance
    
    # Organization configuration
    entry_points = Column(JSON, nullable=False, default=list)  # List of agent IDs that can start workflows
    max_execution_time_minutes = Column(Integer, nullable=False, default=120)
    require_human_supervision = Column(Boolean, nullable=False, default=True)
    allow_parallel_execution = Column(Boolean, nullable=False, default=True)
    
    # Agent organization data stored as JSON
    agents_data = Column(JSON, nullable=False, default=list)  # List of agent nodes with full data
    connections_data = Column(JSON, nullable=False, default=list)  # List of agent connections
    
    # Metadata and tracking
    usage_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="active")  # 'active', 'inactive', 'draft', 'archived'
    template_metadata = Column(JSON, nullable=True, default=dict)  # Additional metadata
    
    # Audit fields
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Legacy agent organizations table - keeping for backward compatibility during migration
class AgentOrganizationTable(Base):
    __tablename__ = "agent_organizations"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=False)
    
    # Template relationship (now points to agent_templates)
    agent_template_id = Column(String, ForeignKey("agent_templates.id"), nullable=True, index=True)
    
    # Organization configuration
    entry_points = Column(JSON, nullable=False, default=list)  # List of agent IDs that can start workflows
    max_execution_time_minutes = Column(Integer, nullable=False, default=120)
    require_human_supervision = Column(Boolean, nullable=False, default=True)
    allow_parallel_execution = Column(Boolean, nullable=False, default=True)
    
    # Agent organization data stored as JSON
    agents_data = Column(JSON, nullable=False, default=list)  # List of agent nodes with full data
    connections_data = Column(JSON, nullable=False, default=list)  # List of agent connections
    
    # Metadata and tracking
    usage_count = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="active")  # 'active', 'inactive', 'archived'
    organization_metadata = Column(JSON, nullable=True, default=dict)  # Additional metadata
    
    # Audit fields
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Workflow Executions table model
class WorkflowExecutionTable(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(String, primary_key=True, index=True)
    workflow_template_id = Column(String, ForeignKey("workflow_templates.id"), nullable=False, index=True)
    organization_id = Column(String, ForeignKey("agent_organizations.id"), nullable=True, index=True)
    
    # Execution state
    status = Column(String, nullable=False, default="pending", index=True)  # pending, running, paused, completed, failed, cancelled
    current_tasks = Column(JSON, nullable=False, default=list)
    completed_tasks = Column(JSON, nullable=False, default=list)
    failed_tasks = Column(JSON, nullable=False, default=list)
    
    # Execution data
    execution_context = Column(JSON, nullable=False, default=dict)
    
    # Human interaction
    human_approvals_pending = Column(JSON, nullable=False, default=list)
    human_feedback = Column(JSON, nullable=False, default=list)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    estimated_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    initiated_by = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Performance tracking
    agent_actions = Column(JSON, nullable=False, default=list)
    error_log = Column(JSON, nullable=False, default=list)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Workflow Tasks table model
class WorkflowTaskTable(Base):
    __tablename__ = "workflow_tasks"
    
    id = Column(String, primary_key=True, index=True)
    execution_id = Column(String, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Task details
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    objective = Column(String(1000), nullable=True)
    completion_criteria = Column(String(1000), nullable=True)
    
    # Task state
    status = Column(String, nullable=False, default="pending", index=True)
    assigned_agent_id = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Dependencies and results
    dependencies = Column(JSON, nullable=False, default=list)
    context = Column(JSON, nullable=False, default=dict)
    results = Column(JSON, nullable=False, default=dict)
    human_feedback = Column(String(2000), nullable=True)
    
    # Metadata
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