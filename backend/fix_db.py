#!/usr/bin/env python3
"""
Fix database creation with proper imports
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

async def fix_database():
    """Fix database creation with proper table registration"""
    print("🔧 Fixing Database Creation")
    print("=" * 50)
    
    try:
        # Remove existing database file
        db_file = "/Users/sanjay/Lab/Fuschia-alfa/backend/fuschia_users.db"
        if os.path.exists(db_file):
            os.remove(db_file)
            print("✅ Removed existing database file")
        
        # Import everything needed - this ensures UserTable is registered
        from app.db.postgres import Base, UserTable, engine, AsyncSessionLocal
        from app.models.user import UserCreate, UserRole
        from sqlalchemy import text
        
        print("✅ Imports successful")
        
        # Check metadata registration
        print(f"📊 Tables in metadata: {list(Base.metadata.tables.keys())}")
        
        if 'users' not in Base.metadata.tables:
            print("❌ UserTable not registered! Let's force registration...")
            
            # Force table definition
            from sqlalchemy import Column, String, Boolean, DateTime
            from datetime import datetime
            
            # Ensure the table is in metadata
            if not hasattr(UserTable, '__table__'):
                print("❌ UserTable.__table__ not found")
                return False
            
        print("✅ UserTable found in metadata")
        
        # Create tables with explicit error handling
        print("Creating database schema...")
        try:
            async with engine.begin() as conn:
                # Drop existing tables first
                await conn.run_sync(Base.metadata.drop_all)
                print("✅ Dropped existing tables")
                
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                print("✅ Created new tables")
                
        except Exception as schema_error:
            print(f"❌ Schema creation failed: {schema_error}")
            return False
        
        # Verify tables were created
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Tables created: {tables}")
            
            if 'users' not in tables:
                print("❌ Users table still not created!")
                return False
        
        # Now create users
        print("Creating users...")
        
        # Use direct import to ensure service has the right imports
        from app.services.postgres_user_service import postgres_user_service
        
        # Create admin user
        admin_user = UserCreate(
            email="admin@fuschia.com",
            full_name="Fuschia Admin",
            password="admin123",
            role=UserRole.ADMIN
        )
        
        try:
            created_admin = await postgres_user_service.create_user(admin_user)
            print(f"✅ Admin user created: {created_admin.email}")
        except Exception as admin_error:
            print(f"❌ Admin creation failed: {admin_error}")
            return False
        
        # Create your user
        your_user = UserCreate(
            email="sanjay.raina@optumis.com",
            full_name="Sanjay Raina",
            password="sanjay123",
            role=UserRole.PROCESS_OWNER
        )
        
        try:
            created_user = await postgres_user_service.create_user(your_user)
            print(f"✅ Your user created: {created_user.email}")
        except Exception as user_error:
            print(f"❌ User creation failed: {user_error}")
            return False
        
        # Verify everything works
        print("\n🧪 Testing authentication...")
        auth_test = await postgres_user_service.authenticate_user("sanjay.raina@optumis.com", "sanjay123")
        if auth_test:
            print(f"✅ Authentication test passed: {auth_test.email}")
        else:
            print("❌ Authentication test failed")
            return False
        
        # Final verification
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"✅ Final user count: {count}")
        
        print("\n🎉 Database fix complete!")
        print("\n📋 Login Credentials:")
        print("   Admin: admin@fuschia.com / admin123")
        print("   Your User: sanjay.raina@optumis.com / sanjay123")
        
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_database())
    if success:
        print("\n✅ Ready to start FastAPI server!")
        print("Run: python -m uvicorn app.main:app --reload")
    else:
        print("\n❌ Fix failed")
        sys.exit(1)