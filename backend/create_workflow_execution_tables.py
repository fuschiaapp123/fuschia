#!/usr/bin/env python3
"""
Database migration script to create workflow execution tables.
Run this script to add the new workflow_executions and workflow_tasks tables to your database.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.postgres import init_db, test_db_connection, engine, Base
from app.db.postgres import WorkflowExecutionTable, WorkflowTaskTable
import structlog

logger = structlog.get_logger()

async def create_workflow_execution_tables():
    """Create the workflow execution tables"""
    try:
        print("🔄 Starting workflow execution tables creation...")
        
        # Test database connection first
        print("🔗 Testing database connection...")
        connection_ok = await test_db_connection()
        if not connection_ok:
            print("❌ Database connection failed!")
            return False
        print("✅ Database connection successful!")
        
        # Create all tables (including the new ones)
        print("🏗️  Creating database tables...")
        async with engine.begin() as conn:
            # This will create all tables defined in Base.metadata, including our new ones
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Workflow execution tables created successfully!")
        print(f"   - workflow_executions table: {WorkflowExecutionTable.__tablename__}")
        print(f"   - workflow_tasks table: {WorkflowTaskTable.__tablename__}")
        
        # Verify tables were created by checking their existence
        print("🔍 Verifying table creation...")
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('workflow_executions', 'workflow_tasks')"
                    if str(engine.url).startswith('sqlite') else
                    "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public' AND tablename IN ('workflow_executions', 'workflow_tasks')"
                ).fetchall()
            )
            
            if len(result) >= 2:
                print("✅ Tables verified successfully!")
                for row in result:
                    print(f"   - Table found: {row[0]}")
            else:
                print(f"⚠️  Warning: Only {len(result)} tables found, expected 2")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create workflow execution tables: {e}")
        logger.error("Table creation failed", error=str(e))
        return False

async def main():
    """Main function"""
    print("=" * 60)
    print("Fuschia Workflow Execution Tables Migration")
    print("=" * 60)
    
    success = await create_workflow_execution_tables()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your FastAPI backend server")
        print("2. Test workflow execution from the Process Designer")
        print("3. Check the Workflow Executions dashboard")
    else:
        print("\n💥 Migration failed!")
        print("Please check the error messages above and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)