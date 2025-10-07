#!/usr/bin/env python3
"""
Script to create the new database tables (workflow_templates, agent_templates)
"""
import asyncio
import sys

# Add the backend directory to the Python path
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

async def create_new_tables():
    """Create the new database tables"""
    print("🗄️  Creating New Database Tables")
    print("=" * 40)
    
    try:
        # Import after path setup
        from app.db.postgres import (
            AsyncSessionLocal, engine, Base
        )
        from sqlalchemy import text
        
        # Test connection first
        print("Testing database connection...")
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Create all tables (this will create new ones and skip existing ones)
        print("Creating new database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/updated successfully")
        
        # Verify the new tables exist
        print("\nVerifying new tables...")
        async with AsyncSessionLocal() as session:
            # Check workflow_templates table
            try:
                await session.execute(text("SELECT COUNT(*) FROM workflow_templates"))
                print("✅ workflow_templates table exists")
            except Exception as e:
                print(f"❌ workflow_templates table issue: {e}")
            
            # Check agent_templates table
            try:
                await session.execute(text("SELECT COUNT(*) FROM agent_templates"))
                print("✅ agent_templates table exists")
            except Exception as e:
                print(f"❌ agent_templates table issue: {e}")
            
            # Check legacy tables still exist
            try:
                await session.execute(text("SELECT COUNT(*) FROM templates"))
                print("✅ templates (legacy) table exists")
            except Exception as e:
                print(f"❌ templates (legacy) table issue: {e}")
            
            try:
                await session.execute(text("SELECT COUNT(*) FROM agent_organizations"))
                print("✅ agent_organizations table exists")
            except Exception as e:
                print(f"❌ agent_organizations table issue: {e}")
        
        print("\n🎉 Table creation/verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def show_table_info():
    """Show information about the database tables"""
    print("\n📊 Database Table Information")
    print("=" * 40)
    
    try:
        from app.db.postgres import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as session:
            # For SQLite, show table list
            try:
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
                tables = result.fetchall()
                print("📋 Available tables:")
                for table in tables:
                    print(f"   - {table[0]}")
            except:
                # For PostgreSQL, show table list
                try:
                    result = await session.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        ORDER BY table_name
                    """))
                    tables = result.fetchall()
                    print("📋 Available tables:")
                    for table in tables:
                        print(f"   - {table[0]}")
                except Exception as e:
                    print(f"Could not list tables: {e}")
        
    except Exception as e:
        print(f"❌ Failed to show table info: {e}")

if __name__ == "__main__":
    success = asyncio.run(create_new_tables())
    if success:
        asyncio.run(show_table_info())
        print("\n✅ Ready! New tables are available.")
        print("\nNext steps:")
        print("1. Run existing workflows to test compatibility")
        print("2. Use the new agent template methods in AgentOrganizationService")
        print("3. Create workflow templates using TemplateService")
    else:
        print("\n❌ Table creation failed")
        sys.exit(1)