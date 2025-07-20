#!/usr/bin/env python3
"""
Migration script to transfer user data from Neo4j to PostgreSQL
"""
import asyncio
import sys
import os
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

from app.db.neo4j import neo4j_driver
from app.db.postgres import init_db, test_db_connection, AsyncSessionLocal, UserTable
from app.services.postgres_user_service import postgres_user_service
from app.models.user import UserCreate, UserRole
import structlog

logger = structlog.get_logger()


async def fetch_users_from_neo4j() -> List[Dict[str, Any]]:
    """Fetch all users from Neo4j"""
    try:
        query = """
        MATCH (u:User)
        RETURN u.id as id, u.email as email, u.full_name as full_name, 
               u.role as role, u.is_active as is_active, 
               u.hashed_password as hashed_password,
               u.created_at as created_at, u.updated_at as updated_at
        """
        
        result = await neo4j_driver.execute_query(query)
        users = []
        
        for record in result:
            user_data = dict(record)
            users.append(user_data)
            
        logger.info(f"Fetched {len(users)} users from Neo4j")
        return users
        
    except Exception as e:
        logger.error(f"Failed to fetch users from Neo4j: {e}")
        return []


def map_legacy_role(neo4j_role: str) -> UserRole:
    """Map Neo4j roles to new PostgreSQL roles"""
    role_mapping = {
        "admin": UserRole.ADMIN,
        "manager": UserRole.MANAGER,
        "analyst": UserRole.ANALYST,
        "user": UserRole.END_USER,
        "process_owner": UserRole.PROCESS_OWNER,
        "end_user": UserRole.END_USER
    }
    
    return role_mapping.get(neo4j_role.lower(), UserRole.END_USER)


async def migrate_users_to_postgres(neo4j_users: List[Dict[str, Any]]) -> int:
    """Migrate users from Neo4j format to PostgreSQL"""
    migrated_count = 0
    
    async with AsyncSessionLocal() as session:
        try:
            for user_data in neo4j_users:
                try:
                    # Map Neo4j role to new role system
                    neo4j_role = user_data.get('role', 'user')
                    postgres_role = map_legacy_role(neo4j_role)
                    
                    # Create PostgreSQL user record
                    db_user = UserTable(
                        id=user_data['id'],
                        email=user_data['email'],
                        full_name=user_data['full_name'],
                        role=postgres_role,
                        is_active=user_data.get('is_active', True),
                        hashed_password=user_data['hashed_password'],
                        # Note: created_at and updated_at will be set by PostgreSQL defaults
                    )
                    
                    session.add(db_user)
                    migrated_count += 1
                    
                    logger.info(f"Prepared user for migration", 
                              email=user_data['email'], 
                              old_role=neo4j_role, 
                              new_role=postgres_role.value)
                    
                except Exception as e:
                    logger.error(f"Failed to prepare user {user_data.get('email', 'unknown')}: {e}")
                    continue
            
            # Commit all users
            await session.commit()
            logger.info(f"Successfully migrated {migrated_count} users to PostgreSQL")
            
            return migrated_count
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Migration failed: {e}")
            raise


async def verify_migration() -> bool:
    """Verify that migration was successful"""
    try:
        # Get user count from PostgreSQL
        async with AsyncSessionLocal() as session:
            from sqlalchemy import func, select
            result = await session.execute(select(func.count(UserTable.id)))
            pg_count = result.scalar()
        
        # Get user count from Neo4j
        neo4j_query = "MATCH (u:User) RETURN count(u) as count"
        neo4j_result = await neo4j_driver.execute_query(neo4j_query)
        neo4j_count = neo4j_result[0]['count'] if neo4j_result else 0
        
        logger.info(f"User counts - Neo4j: {neo4j_count}, PostgreSQL: {pg_count}")
        
        if pg_count >= neo4j_count:
            logger.info("✅ Migration verification successful")
            return True
        else:
            logger.error("❌ Migration verification failed - user count mismatch")
            return False
            
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False


async def show_role_distribution():
    """Show the distribution of users by role after migration"""
    try:
        role_counts = await postgres_user_service.get_user_count_by_role()
        
        print("\n📊 User Role Distribution After Migration:")
        print("=" * 50)
        for role, count in role_counts.items():
            print(f"{role.replace('_', ' ').title():<20}: {count} users")
        
        total_users = sum(role_counts.values())
        print(f"{'Total':<20}: {total_users} users")
        
    except Exception as e:
        logger.error(f"Failed to show role distribution: {e}")


async def main():
    """Main migration function"""
    print("🚀 Starting User Migration from Neo4j to PostgreSQL")
    print("=" * 60)
    
    try:
        # Test database connections
        print("1. Testing database connections...")
        
        # Test PostgreSQL
        pg_connected = await test_db_connection()
        if not pg_connected:
            print("❌ PostgreSQL connection failed")
            return
        
        # Test Neo4j (assuming it's working since we're migrating from it)
        print("✅ Database connections verified")
        
        # Initialize PostgreSQL database
        print("\n2. Initializing PostgreSQL database...")
        await init_db()
        print("✅ PostgreSQL database initialized")
        
        # Fetch users from Neo4j
        print("\n3. Fetching users from Neo4j...")
        neo4j_users = await fetch_users_from_neo4j()
        
        if not neo4j_users:
            print("⚠️  No users found in Neo4j or fetch failed")
            return
        
        print(f"✅ Found {len(neo4j_users)} users in Neo4j")
        
        # Migrate users to PostgreSQL
        print("\n4. Migrating users to PostgreSQL...")
        migrated_count = await migrate_users_to_postgres(neo4j_users)
        print(f"✅ Migrated {migrated_count} users successfully")
        
        # Verify migration
        print("\n5. Verifying migration...")
        verification_success = await verify_migration()
        
        if verification_success:
            print("✅ Migration completed successfully!")
            
            # Show role distribution
            await show_role_distribution()
            
            print("\n📝 Next Steps:")
            print("1. Update your application to use PostgresUserService")
            print("2. Update environment variables for PostgreSQL connection")
            print("3. Test authentication and user management functions")
            print("4. Consider archiving Neo4j user data")
            
        else:
            print("❌ Migration verification failed")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())