#!/usr/bin/env python3
"""
Reset and recreate SQLite database
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

async def reset_database():
    """Reset database and create fresh tables"""
    print("🗑️  Resetting Database")
    print("=" * 40)
    
    try:
        # Remove existing database file
        db_file = "/Users/sanjay/Lab/Fuschia-alfa/backend/fuschia_users.db"
        if os.path.exists(db_file):
            os.remove(db_file)
            print("✅ Removed existing database file")
        
        # Import after path setup
        from app.db.postgres import Base, engine, AsyncSessionLocal
        from app.services.postgres_user_service import postgres_user_service
        from app.models.user import UserCreate, UserRole
        from sqlalchemy import text
        
        print("Creating new database schema...")
        
        # Create tables synchronously for better error handling
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database schema created")
        
        # Test connection
        print("Testing database connection...")
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            print(f"✅ Found tables: {[table[0] for table in tables]}")
        
        # Create users
        print("Creating admin user...")
        admin_user = UserCreate(
            email="admin@fuschia.com",
            full_name="Fuschia Admin",
            password="admin123",
            role=UserRole.ADMIN
        )
        
        created_admin = await postgres_user_service.create_user(admin_user)
        print(f"✅ Admin user created: {created_admin.email}")
        
        # Create your user
        print("Creating your user...")
        your_user = UserCreate(
            email="sanjay.raina@optumis.com",
            full_name="Sanjay Raina", 
            password="sanjay123",
            role=UserRole.PROCESS_OWNER
        )
        
        created_user = await postgres_user_service.create_user(your_user)
        print(f"✅ Your user created: {created_user.email}")
        
        # Verify users exist
        print("Verifying users...")
        admin_check = await postgres_user_service.get_user_by_email("admin@fuschia.com")
        user_check = await postgres_user_service.get_user_by_email("sanjay.raina@optumis.com")
        
        if admin_check and user_check:
            print("✅ All users verified in database")
        else:
            print("❌ User verification failed")
            return False
        
        print("\n🎉 Database reset complete!")
        print("\n📋 Login Credentials:")
        print("   Admin: admin@fuschia.com / admin123")
        print("   Your User: sanjay.raina@optumis.com / sanjay123")
        
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(reset_database())
    if success:
        print("\n✅ Ready to start FastAPI server!")
        print("Run: python -m uvicorn app.main:app --reload")
    else:
        print("\n❌ Reset failed")
        sys.exit(1)