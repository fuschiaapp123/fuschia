#!/usr/bin/env python3
"""Simple database initialization script to create users only"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.postgres import init_database
from app.services.postgres_user_service import postgres_user_service
from app.models.user import UserCreate, UserRole


async def create_users():
    """Create sample users"""

    sample_users = [
        {
            "email": "admin@fuschia.com",
            "password": "admin123",
            "role": UserRole.ADMIN,
            "full_name": "System Administrator"
        },
        {
            "email": "manager@fuschia.io",
            "password": "manager123",
            "role": UserRole.MANAGER,
            "full_name": "Process Manager"
        },
        {
            "email": "analyst@fuschia.io",
            "password": "analyst123",
            "role": UserRole.ANALYST,
            "full_name": "Business Analyst"
        },
        {
            "email": "user@fuschia.io",
            "password": "userpassword123",
            "role": UserRole.USER,
            "full_name": "End User"
        }
    ]

    users = []

    for user_data in sample_users:
        try:
            user_create = UserCreate(**user_data)
            user = await postgres_user_service.create_user(user_create)
            users.append(user)
            print(f"Created user: {user.email} ({user.role})")
        except Exception as e:
            print(f"Error creating user {user_data['email']}: {str(e)}")
            continue

    return users


async def main():
    print("Starting simple Fuschia database initialization...")

    # Initialize database tables
    print("Initializing PostgreSQL database...")
    await init_database()
    print("✅ PostgreSQL database initialized")

    # Create users
    print("\nCreating sample users...")
    users = await create_users()

    if users:
        print("\n✅ Database initialization completed successfully!")
        print(f"Created {len(users)} users")
        print("\nSample user credentials:")
        print("Admin: admin@fuschia.com / admin123")
        print("Manager: manager@fuschia.io / manager123")
        print("Analyst: analyst@fuschia.io / analyst123")
        print("User: user@fuschia.io / userpassword123")
    else:
        print("❌ No users were created")


if __name__ == "__main__":
    asyncio.run(main())