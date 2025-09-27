from typing import Optional, List
from datetime import datetime
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from app.db.postgres import UserTable, AsyncSessionLocal
from app.models.user import User, UserCreate, UserUpdate, UserInDB, UserRole
from app.auth.password import get_password_hash, verify_password

logger = structlog.get_logger()


class PostgresUserService:
    """PostgreSQL-based user service with role-based access control"""
    
    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user in PostgreSQL"""
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_create.password)
        
        async with AsyncSessionLocal() as session:
            try:
                db_user = UserTable(
                    id=user_id,
                    email=user_create.email,
                    full_name=user_create.full_name,
                    role=user_create.role.value if isinstance(user_create.role, UserRole) else user_create.role,
                    is_active=user_create.is_active,
                    hashed_password=hashed_password
                )
                
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
                
                logger.info("User created successfully", user_id=user_id, email=user_create.email, role=user_create.role)
                
                return User(
                    id=db_user.id,
                    username=db_user.email.split('@')[0],  # Use email prefix as username
                    email=db_user.email,
                    role=UserRole(db_user.role) if isinstance(db_user.role, str) else db_user.role,
                    is_active=db_user.is_active,
                    created_at=db_user.created_at
                )
                
            except IntegrityError as e:
                await session.rollback()
                logger.error("User creation failed - email already exists", email=user_create.email, error=str(e))
                raise ValueError(f"User with email {user_create.email} already exists")
            except Exception as e:
                await session.rollback()
                logger.error("User creation failed", error=str(e))
                raise Exception(f"Failed to create user: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(UserTable).where(UserTable.email == email)
                )
                db_user = result.scalar_one_or_none()
                
                if db_user:
                    return UserInDB(
                        id=db_user.id,
                        email=db_user.email,
                        full_name=db_user.full_name,
                        role=UserRole(db_user.role) if isinstance(db_user.role, str) else db_user.role,
                        is_active=db_user.is_active,
                        hashed_password=db_user.hashed_password,
                        created_at=db_user.created_at
                    )
                return None
                
            except Exception as e:
                logger.error("Failed to get user by email", email=email, error=str(e))
                return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(UserTable).where(UserTable.id == user_id)
                )
                db_user = result.scalar_one_or_none()
                
                if db_user:
                    return User(
                        id=db_user.id,
                        username=db_user.email.split('@')[0],
                        email=db_user.email,
                        full_name=db_user.full_name,
                        role=UserRole(db_user.role) if isinstance(db_user.role, str) else db_user.role,
                        is_active=db_user.is_active,
                        created_at=db_user.created_at,
                        updated_at=db_user.updated_at
                    )
                return None
                
            except Exception as e:
                logger.error("Failed to get user by ID", user_id=user_id, error=str(e))
                return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user credentials"""
        user = await self.get_user_by_email(email)
        if not user:
            logger.warning("Authentication failed - user not found", email=email)
            return None
        
        if not user.is_active:
            logger.warning("Authentication failed - user inactive", email=email)
            return None
            
        if not verify_password(password, user.hashed_password):
            logger.warning("Authentication failed - invalid password", email=email)
            return None
            
        logger.info("User authenticated successfully", email=email, role=user.role)
        return user
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        async with AsyncSessionLocal() as session:
            try:
                # Build update dictionary
                update_data = {}
                if user_update.email is not None:
                    update_data["email"] = user_update.email
                if user_update.full_name is not None:
                    update_data["full_name"] = user_update.full_name
                if user_update.role is not None:
                    update_data["role"] = user_update.role.value if isinstance(user_update.role, UserRole) else user_update.role
                if user_update.is_active is not None:
                    update_data["is_active"] = user_update.is_active
                
                if not update_data:
                    return await self.get_user_by_id(user_id)
                
                update_data["updated_at"] = datetime.utcnow()
                
                # Execute update
                result = await session.execute(
                    update(UserTable)
                    .where(UserTable.id == user_id)
                    .values(**update_data)
                    .returning(UserTable)
                )
                
                db_user = result.scalar_one_or_none()
                if db_user:
                    await session.commit()
                    logger.info("User updated successfully", user_id=user_id, updated_fields=list(update_data.keys()))
                    
                    return User(
                        id=db_user.id,
                        username=db_user.email.split('@')[0],
                        email=db_user.email,
                        full_name=db_user.full_name,
                        role=UserRole(db_user.role) if isinstance(db_user.role, str) else db_user.role,
                        is_active=db_user.is_active,
                        created_at=db_user.created_at,
                        updated_at=db_user.updated_at
                    )
                else:
                    await session.rollback()
                    logger.warning("User update failed - user not found", user_id=user_id)
                    return None
                    
            except IntegrityError as e:
                await session.rollback()
                logger.error("User update failed - integrity constraint", user_id=user_id, error=str(e))
                raise ValueError("Email already exists or other constraint violation")
            except Exception as e:
                await session.rollback()
                logger.error("User update failed", user_id=user_id, error=str(e))
                raise Exception(f"Failed to update user: {str(e)}")
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active to False)"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    update(UserTable)
                    .where(UserTable.id == user_id)
                    .values(is_active=False, updated_at=datetime.utcnow())
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info("User deactivated successfully", user_id=user_id)
                    return True
                else:
                    logger.warning("User deactivation failed - user not found", user_id=user_id)
                    return False
                    
            except Exception as e:
                await session.rollback()
                logger.error("User deactivation failed", user_id=user_id, error=str(e))
                return False
    
    async def get_users_by_role(self, role: UserRole, active_only: bool = True) -> List[User]:
        """Get all users with a specific role"""
        async with AsyncSessionLocal() as session:
            try:
                query = select(UserTable).where(UserTable.role == (role.value if isinstance(role, UserRole) else role))
                if active_only:
                    query = query.where(UserTable.is_active == True)
                
                result = await session.execute(query)
                db_users = result.scalars().all()
                
                return [
                    User(
                        id=db_user.id,
                        username=db_user.email.split('@')[0],
                        email=db_user.email,
                        full_name=db_user.full_name,
                        role=UserRole(db_user.role) if isinstance(db_user.role, str) else db_user.role,
                        is_active=db_user.is_active,
                        created_at=db_user.created_at,
                        updated_at=db_user.updated_at
                    )
                    for db_user in db_users
                ]
                
            except Exception as e:
                logger.error("Failed to get users by role", role=role, error=str(e))
                return []
    
    async def get_all_users(self, active_only: bool = True, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        async with AsyncSessionLocal() as session:
            try:
                query = select(UserTable)
                if active_only:
                    query = query.where(UserTable.is_active == True)
                
                query = query.limit(limit).offset(offset).order_by(UserTable.created_at.desc())
                
                result = await session.execute(query)
                db_users = result.scalars().all()
                
                return [
                    User(
                        id=db_user.id,
                        username=db_user.email.split('@')[0],
                        email=db_user.email,
                        full_name=db_user.full_name,
                        role=UserRole(db_user.role) if isinstance(db_user.role, str) else db_user.role,
                        is_active=db_user.is_active,
                        created_at=db_user.created_at,
                        updated_at=db_user.updated_at
                    )
                    for db_user in db_users
                ]
                
            except Exception as e:
                logger.error("Failed to get all users", error=str(e))
                return []
    
    async def user_has_permission(self, user_id: str, required_roles: List[UserRole]) -> bool:
        """Check if user has required role permissions"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return False
        
        return user.role in required_roles
    
    async def get_user_count_by_role(self) -> dict:
        """Get count of users by role"""
        async with AsyncSessionLocal() as session:
            try:
                from sqlalchemy import func
                result = await session.execute(
                    select(UserTable.role, func.count(UserTable.id))
                    .where(UserTable.is_active == True)
                    .group_by(UserTable.role)
                )
                
                role_counts = {}
                for role, count in result.all():
                    # role is already a string from the database
                    role_counts[role] = count
                
                return role_counts
                
            except Exception as e:
                logger.error("Failed to get user count by role", error=str(e))
                return {}
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password"""
        async with AsyncSessionLocal() as session:
            try:
                # Get user with password hash
                result = await session.execute(
                    select(UserTable).where(UserTable.id == user_id)
                )
                db_user = result.scalar_one_or_none()
                
                if not db_user:
                    logger.warning("Password change failed - user not found", user_id=user_id)
                    return False
                
                # Verify current password
                if not verify_password(current_password, db_user.hashed_password):
                    logger.warning("Password change failed - invalid current password", user_id=user_id)
                    return False
                
                # Hash new password
                new_hashed_password = get_password_hash(new_password)
                
                # Update password
                result = await session.execute(
                    update(UserTable)
                    .where(UserTable.id == user_id)
                    .values(
                        hashed_password=new_hashed_password,
                        updated_at=datetime.utcnow()
                    )
                )
                
                if result.rowcount > 0:
                    await session.commit()
                    logger.info("Password changed successfully", user_id=user_id)
                    return True
                else:
                    logger.warning("Password change failed - no rows updated", user_id=user_id)
                    return False
                    
            except Exception as e:
                await session.rollback()
                logger.error("Password change failed", user_id=user_id, error=str(e))
                return False

    async def admin_reset_password(self, user_id: str, new_password: str) -> bool:
        """Admin-only password reset without requiring current password"""
        async with AsyncSessionLocal() as session:
            try:
                # Hash new password
                new_hashed_password = get_password_hash(new_password)

                # Update password
                result = await session.execute(
                    update(UserTable)
                    .where(UserTable.id == user_id)
                    .values(
                        hashed_password=new_hashed_password,
                        updated_at=datetime.utcnow()
                    )
                )

                if result.rowcount > 0:
                    await session.commit()
                    logger.info("Admin password reset successful", user_id=user_id)
                    return True
                else:
                    logger.warning("Admin password reset failed - user not found", user_id=user_id)
                    return False

            except Exception as e:
                await session.rollback()
                logger.error("Admin password reset failed", user_id=user_id, error=str(e))
                return False


# Create global instance
postgres_user_service = PostgresUserService()