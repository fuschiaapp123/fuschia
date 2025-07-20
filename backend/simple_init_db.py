#!/usr/bin/env python3
"""
Simple SQLite database initialization
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

async def init_simple_db():
    """Initialize database with proper error handling"""
    print("🗄️  Initializing Database")
    print("=" * 40)
    
    try:
        # Import after path setup
        from app.db.postgres import init_db, AsyncSessionLocal, engine
        from app.services.postgres_user_service import postgres_user_service
        from app.models.user import UserCreate, UserRole
        from sqlalchemy import text
        
        # Test connection first
        print("Testing database connection...")
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            print("✅ Database connection successful")
        
        # Initialize database schema
        print("Creating database tables...")
        await init_db()
        print("✅ Database schema initialized")
        
        # Create admin user
        print("Creating admin user...")
        try:
            admin_user = UserCreate(
                email="admin@fuschia.com",
                full_name="Fuschia Admin",
                password="admin123",
                role=UserRole.ADMIN
            )
            
            # Check if admin already exists
            existing_admin = await postgres_user_service.get_user_by_email("admin@fuschia.com")
            if existing_admin:
                print("✅ Admin user already exists")
            else:
                created_admin = await postgres_user_service.create_user(admin_user)
                print(f"✅ Admin user created: {created_admin.email}")
            
            # Create your user
            your_user = UserCreate(
                email="sanjay.raina@optumis.com",
                full_name="Sanjay Raina",
                password="sanjay123",
                role=UserRole.PROCESS_OWNER
            )
            
            existing_user = await postgres_user_service.get_user_by_email("sanjay.raina@optumis.com")
            if existing_user:
                print("✅ Your user already exists")
            else:
                created_user = await postgres_user_service.create_user(your_user)
                print(f"✅ Your user created: {created_user.email}")
            
            print("\n🎉 Database initialization complete!")
            print("\n📋 Login Credentials:")
            print("   Admin: admin@fuschia.com / admin123")
            print("   Your User: sanjay.raina@optumis.com / sanjay123")
            
            return True
            
        except Exception as user_error:
            print(f"❌ User creation failed: {user_error}")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(init_simple_db())
    if success:
        print("\n✅ Ready to start FastAPI server!")
        print("Run: python -m uvicorn app.main:app --reload")
    else:
        print("\n❌ Initialization failed")
        sys.exit(1)