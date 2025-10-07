from fastapi import APIRouter, HTTPException
from app.db.postgres import init_db, test_db_connection, engine
import structlog

router = APIRouter()
logger = structlog.get_logger()

@router.post("/init")
async def initialize_database():
    """
    Initialize database tables - creates all tables defined in models
    """
    try:
        logger.info("Manual database initialization requested")
        
        # Test connection first
        connection_ok = await test_db_connection()
        if not connection_ok:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Initialize all tables
        await init_db()
        
        # Verify specific workflow execution tables exist
        async with engine.begin() as conn:
            # Get table names (SQLite vs PostgreSQL compatible)
            if str(engine.url).startswith('sqlite'):
                result = await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    ).fetchall()
                )
            else:
                result = await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public' ORDER BY tablename"
                    ).fetchall()
                )
            
            table_names = [row[0] for row in result]
            
            # Check for our new tables
            new_tables = ['workflow_executions', 'workflow_tasks']
            found_new_tables = [table for table in new_tables if table in table_names]
            
            logger.info("Database initialization completed", 
                       total_tables=len(table_names),
                       new_tables_found=len(found_new_tables))
            
            return {
                "status": "success",
                "message": "Database initialized successfully",
                "total_tables": len(table_names),
                "all_tables": table_names,
                "new_workflow_tables": found_new_tables,
                "workflow_execution_tables_created": len(found_new_tables) == len(new_tables)
            }
            
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

@router.get("/status")
async def get_database_status():
    """
    Get database connection status and table information
    """
    try:
        # Test connection
        connection_ok = await test_db_connection()
        
        if not connection_ok:
            return {
                "status": "disconnected",
                "message": "Database connection failed",
                "connected": False
            }
        
        # Get table information
        async with engine.begin() as conn:
            if str(engine.url).startswith('sqlite'):
                result = await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    ).fetchall()
                )
            else:
                result = await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public' ORDER BY tablename"
                    ).fetchall()
                )
            
            table_names = [row[0] for row in result]
            
            # Check for workflow execution tables
            workflow_tables = ['workflow_executions', 'workflow_tasks']
            workflow_tables_exist = all(table in table_names for table in workflow_tables)
            
            return {
                "status": "connected",
                "message": "Database connection successful",
                "connected": True,
                "database_type": "sqlite" if str(engine.url).startswith('sqlite') else "postgresql",
                "total_tables": len(table_names),
                "all_tables": table_names,
                "workflow_execution_tables_exist": workflow_tables_exist,
                "workflow_tables_found": [table for table in workflow_tables if table in table_names]
            }
            
    except Exception as e:
        logger.error("Database status check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Database status check failed: {str(e)}")