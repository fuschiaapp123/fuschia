from typing import Optional, List
from datetime import datetime
import uuid
import structlog
from neo4j.time import DateTime as Neo4jDateTime

from app.db.neo4j import neo4j_driver
from app.models.user import User, UserCreate, UserUpdate, UserInDB
from app.auth.password import get_password_hash, verify_password

logger = structlog.get_logger()


def convert_neo4j_datetime(neo4j_dt) -> Optional[datetime]:
    """Convert Neo4j DateTime to Python datetime"""
    if neo4j_dt is None:
        return None
    if isinstance(neo4j_dt, Neo4jDateTime):
        return neo4j_dt.to_native()
    if isinstance(neo4j_dt, datetime):
        return neo4j_dt
    return None


class UserService:
    async def create_user(self, user_create: UserCreate) -> User:
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_create.password)
        
        query = """
        CREATE (u:User {
            id: $id,
            email: $email,
            full_name: $full_name,
            role: $role,
            is_active: $is_active,
            hashed_password: $hashed_password,
            created_at: datetime()
        })
        RETURN u
        """
        
        parameters = {
            "id": user_id,
            "email": user_create.email,
            "full_name": user_create.full_name,
            "role": user_create.role,
            "is_active": user_create.is_active,
            "hashed_password": hashed_password
        }
        
        result = await neo4j_driver.execute_query(query, parameters)
        if result:
            user_data = result[0]["u"]
            return User(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=convert_neo4j_datetime(user_data["created_at"])
            )
        raise Exception("Failed to create user")
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        query = """
        MATCH (u:User {email: $email})
        RETURN u
        """
        
        result = await neo4j_driver.execute_query(query, {"email": email})
        if result:
            user_data = result[0]["u"]
            return UserInDB(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                hashed_password=user_data["hashed_password"],
                created_at=convert_neo4j_datetime(user_data["created_at"]),
                updated_at=convert_neo4j_datetime(user_data.get("updated_at"))
            )
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        query = """
        MATCH (u:User {id: $user_id})
        RETURN u
        """
        
        result = await neo4j_driver.execute_query(query, {"user_id": user_id})
        if result:
            user_data = result[0]["u"]
            return User(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=convert_neo4j_datetime(user_data["created_at"]),
                updated_at=convert_neo4j_datetime(user_data.get("updated_at"))
            )
        return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        update_fields = []
        parameters = {"user_id": user_id, "updated_at": datetime.utcnow()}
        
        if user_update.email is not None:
            update_fields.append("u.email = $email")
            parameters["email"] = user_update.email
        
        if user_update.full_name is not None:
            update_fields.append("u.full_name = $full_name")
            parameters["full_name"] = user_update.full_name
        
        if user_update.role is not None:
            update_fields.append("u.role = $role")
            parameters["role"] = user_update.role
        
        if user_update.is_active is not None:
            update_fields.append("u.is_active = $is_active")
            parameters["is_active"] = user_update.is_active
        
        if not update_fields:
            return await self.get_user_by_id(user_id)
        
        query = f"""
        MATCH (u:User {{id: $user_id}})
        SET {', '.join(update_fields)}, u.updated_at = $updated_at
        RETURN u
        """
        
        result = await neo4j_driver.execute_query(query, parameters)
        if result:
            user_data = result[0]["u"]
            return User(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=convert_neo4j_datetime(user_data["created_at"]),
                updated_at=convert_neo4j_datetime(user_data.get("updated_at"))
            )
        return None