#!/usr/bin/env python3
"""
Initialize SQLite database with admin user
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

from app.db.postgres import init_db, test_db_connection
from app.services.postgres_user_service import postgres_user_service
from app.models.user import UserCreate, UserRole
import structlog

logger = structlog.get_logger()

async def init_sqlite_database():
    """Initialize SQLite database and create admin user"""
    print("🗄️  Initializing SQLite Database")
    print("=" * 50)
    
    try:
        # Test connection
        connected = await test_db_connection()
        if not connected:
            print("❌ Database connection failed")
            return False
        print("✅ Database connection successful")
        
        # Initialize database schema
        await init_db()
        print("✅ Database schema initialized")
        
        # Check if admin user already exists
        existing_admin = await postgres_user_service.get_user_by_email("admin@fuschia.com")
        if existing_admin:
            print("✅ Admin user already exists")
            return True
        
        # Create admin user
        admin_user = UserCreate(
            email="admin@fuschia.com",
            full_name="Fuschia Admin",
            password="admin123",
            role=UserRole.ADMIN
        )
        
        created_admin = await postgres_user_service.create_user(admin_user)
        print(f"✅ Admin user created: {created_admin.email}")
        
        # Create test users for different roles
        test_users = [
            {
                "email": "manager@fuschia.com",
                "full_name": "Test Manager",
                "password": "manager123",
                "role": UserRole.MANAGER
            },
            {
                "email": "analyst@fuschia.com", 
                "full_name": "Test Analyst",
                "password": "analyst123",
                "role": UserRole.ANALYST
            },
            {
                "email": "sanjay.raina@optumis.com",
                "full_name": "Sanjay Raina",
                "password": "sanjay123",
                "role": UserRole.PROCESS_OWNER
            }
        ]
        
        for user_data in test_users:
            existing_user = await postgres_user_service.get_user_by_email(user_data["email"])
            if not existing_user:
                test_user = UserCreate(**user_data)
                created_user = await postgres_user_service.create_user(test_user)
                print(f"✅ User created: {created_user.email} ({created_user.role})")
        
        # Display summary
        print("\n📊 Database Summary:")
        role_counts = await postgres_user_service.get_user_count_by_role()
        for role, count in role_counts.items():
            print(f"   {role}: {count} users")
        
        print("\n🎉 Database initialization complete!")
        print("\n📋 Login Credentials:")
        print("   Admin: admin@fuschia.com / admin123")
        print("   Manager: manager@fuschia.com / manager123") 
        print("   Analyst: analyst@fuschia.com / analyst123")
        print("   Your User: sanjay.raina@optumis.com / sanjay123")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(init_sqlite_database())
    if success:
        print("\n✅ Ready to start FastAPI server!")
    else:
        print("\n❌ Initialization failed")
        sys.exit(1)