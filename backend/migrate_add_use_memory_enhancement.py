#!/usr/bin/env python3
"""
Database migration script to add use_memory_enhancement column to workflow_executions table.
Run this script to add the new column to existing workflow_executions tables.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.postgres import engine, test_db_connection
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

async def add_use_memory_enhancement_column():
    """Add use_memory_enhancement column to workflow_executions table"""
    try:
        print("🔄 Starting use_memory_enhancement column migration...")
        
        # Test database connection first
        print("🔗 Testing database connection...")
        connection_ok = await test_db_connection()
        if not connection_ok:
            print("❌ Database connection failed!")
            return False
        print("✅ Database connection successful!")
        
        # Check if column already exists
        print("🔍 Checking if use_memory_enhancement column already exists...")
        async with engine.begin() as conn:
            # Check column existence (works for PostgreSQL and SQLite)
            if str(engine.url).startswith('sqlite'):
                result = await conn.execute(text(
                    "PRAGMA table_info(workflow_executions)"
                ))
                columns = [row[1] for row in result.fetchall()]  # Column name is at index 1
            else:  # PostgreSQL
                result = await conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='workflow_executions' AND column_name='use_memory_enhancement'"
                ))
                columns = [row[0] for row in result.fetchall()]
            
            if 'use_memory_enhancement' in columns:
                print("✅ Column use_memory_enhancement already exists, skipping migration")
                return True
        
        # Add the column
        print("🏗️  Adding use_memory_enhancement column...")
        async with engine.begin() as conn:
            if str(engine.url).startswith('sqlite'):
                # SQLite syntax
                await conn.execute(text(
                    "ALTER TABLE workflow_executions ADD COLUMN use_memory_enhancement BOOLEAN NOT NULL DEFAULT FALSE"
                ))
            else:  # PostgreSQL
                await conn.execute(text(
                    "ALTER TABLE workflow_executions ADD COLUMN use_memory_enhancement BOOLEAN NOT NULL DEFAULT FALSE"
                ))
        
        print("✅ Column use_memory_enhancement added successfully!")
        
        # Verify column was added
        print("🔍 Verifying column addition...")
        async with engine.begin() as conn:
            if str(engine.url).startswith('sqlite'):
                result = await conn.execute(text(
                    "PRAGMA table_info(workflow_executions)"
                ))
                columns = [row[1] for row in result.fetchall()]
            else:  # PostgreSQL
                result = await conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='workflow_executions' AND column_name='use_memory_enhancement'"
                ))
                columns = [row[0] for row in result.fetchall()]
            
            if 'use_memory_enhancement' in columns:
                print("✅ Column verified successfully!")
            else:
                print("⚠️  Warning: Column verification failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add use_memory_enhancement column: {e}")
        logger.error("Column migration failed", error=str(e))
        return False

async def main():
    """Main function"""
    print("=" * 60)
    print("Fuschia Memory Enhancement Column Migration")
    print("=" * 60)
    
    success = await add_use_memory_enhancement_column()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nThe use_memory_enhancement column has been added to workflow_executions table.")
        print("\nNext steps:")
        print("1. Restart your FastAPI backend server")
        print("2. Test memory enhancement toggle from the Workflow Designer")
        print("3. Verify memory enhancement works in workflow executions")
    else:
        print("\n💥 Migration failed!")
        print("Please check the error messages above and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)