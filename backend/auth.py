"""
Authentication and Authorization system for Fuschia SaaS
Handles user registration, login, JWT tokens, and role-based access control
"""

import jwt
import bcrypt
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles in the system"""
    SUPER_ADMIN = "super_admin"  # Platform administrator
    ORG_ADMIN = "org_admin"      # Organization administrator
    END_USER = "end_user"        # End user/customer service agent

class SubscriptionTier(Enum):
    """Subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

@dataclass
class User:
    """User model"""
    id: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    role: UserRole
    organization_id: str
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class Organization:
    """Organization model for multi-tenancy"""
    id: str
    name: str
    domain: str
    subscription_tier: SubscriptionTier
    admin_user_id: str
    settings: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = None
    trial_ends_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.trial_ends_at is None:
            self.trial_ends_at = datetime.utcnow() + timedelta(days=14)

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self, secret_key: str, neo4j_driver=None):
        self.secret_key = secret_key
        self.neo4j_driver = neo4j_driver
        self.token_expiry = timedelta(hours=24)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'organization_id': user.organization_id,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def create_organization(self, name: str, domain: str, admin_email: str, 
                          admin_password: str, admin_first_name: str, 
                          admin_last_name: str) -> tuple[Organization, User]:
        """Create new organization with admin user"""
        try:
            # Create organization
            org_id = str(uuid.uuid4())
            organization = Organization(
                id=org_id,
                name=name,
                domain=domain,
                subscription_tier=SubscriptionTier.FREE,
                admin_user_id="",  # Will be set after user creation
                settings={}
            )
            
            # Create admin user
            admin_user = User(
                id=str(uuid.uuid4()),
                email=admin_email,
                password_hash=self.hash_password(admin_password),
                first_name=admin_first_name,
                last_name=admin_last_name,
                role=UserRole.ORG_ADMIN,
                organization_id=org_id
            )
            
            # Update organization with admin user ID
            organization.admin_user_id = admin_user.id
            
            # Store in Neo4j
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    # Create organization node
                    session.run("""
                        CREATE (o:Organization {
                            id: $id,
                            name: $name,
                            domain: $domain,
                            subscription_tier: $subscription_tier,
                            admin_user_id: $admin_user_id,
                            settings: $settings,
                            is_active: $is_active,
                            created_at: $created_at,
                            trial_ends_at: $trial_ends_at
                        })
                    """, 
                    id=organization.id,
                    name=organization.name,
                    domain=organization.domain,
                    subscription_tier=organization.subscription_tier.value,
                    admin_user_id=organization.admin_user_id,
                    settings=json.dumps(organization.settings),
                    is_active=organization.is_active,
                    created_at=organization.created_at.isoformat(),
                    trial_ends_at=organization.trial_ends_at.isoformat()
                    )
                    
                    # Create admin user node
                    session.run("""
                        CREATE (u:User {
                            id: $id,
                            email: $email,
                            password_hash: $password_hash,
                            first_name: $first_name,
                            last_name: $last_name,
                            role: $role,
                            organization_id: $organization_id,
                            is_active: $is_active,
                            created_at: $created_at
                        })
                    """,
                    id=admin_user.id,
                    email=admin_user.email,
                    password_hash=admin_user.password_hash,
                    first_name=admin_user.first_name,
                    last_name=admin_user.last_name,
                    role=admin_user.role.value,
                    organization_id=admin_user.organization_id,
                    is_active=admin_user.is_active,
                    created_at=admin_user.created_at.isoformat()
                    )
                    
                    # Create relationship
                    session.run("""
                        MATCH (o:Organization {id: $org_id})
                        MATCH (u:User {id: $user_id})
                        CREATE (u)-[:BELONGS_TO]->(o)
                        CREATE (u)-[:ADMIN_OF]->(o)
                    """, org_id=organization.id, user_id=admin_user.id)
            
            logger.info(f"Created organization {name} with admin {admin_email}")
            return organization, admin_user
            
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            raise
    
    def create_user(self, email: str, password: str, first_name: str, 
                   last_name: str, role: UserRole, organization_id: str) -> User:
        """Create new user in existing organization"""
        try:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                password_hash=self.hash_password(password),
                first_name=first_name,
                last_name=last_name,
                role=role,
                organization_id=organization_id
            )
            
            # Store in Neo4j
            if self.neo4j_driver:
                with self.neo4j_driver.session() as session:
                    session.run("""
                        CREATE (u:User {
                            id: $id,
                            email: $email,
                            password_hash: $password_hash,
                            first_name: $first_name,
                            last_name: $last_name,
                            role: $role,
                            organization_id: $organization_id,
                            is_active: $is_active,
                            created_at: $created_at
                        })
                    """,
                    id=user.id,
                    email=user.email,
                    password_hash=user.password_hash,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role.value,
                    organization_id=user.organization_id,
                    is_active=user.is_active,
                    created_at=user.created_at.isoformat()
                    )
                    
                    # Create relationship to organization
                    session.run("""
                        MATCH (o:Organization {id: $org_id})
                        MATCH (u:User {id: $user_id})
                        CREATE (u)-[:BELONGS_TO]->(o)
                    """, org_id=organization_id, user_id=user.id)
            
            logger.info(f"Created user {email} in organization {organization_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        try:
            if not self.neo4j_driver:
                return None
                
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (u:User {email: $email, is_active: true})
                    RETURN u.id as id, u.email as email, u.password_hash as password_hash,
                           u.first_name as first_name, u.last_name as last_name,
                           u.role as role, u.organization_id as organization_id,
                           u.is_active as is_active, u.created_at as created_at,
                           u.last_login as last_login
                """, email=email)
                
                record = result.single()
                if not record:
                    return None
                
                # Verify password
                if not self.verify_password(password, record['password_hash']):
                    return None
                
                # Create user object
                user = User(
                    id=record['id'],
                    email=record['email'],
                    password_hash=record['password_hash'],
                    first_name=record['first_name'],
                    last_name=record['last_name'],
                    role=UserRole(record['role']),
                    organization_id=record['organization_id'],
                    is_active=record['is_active'],
                    created_at=datetime.fromisoformat(record['created_at']) if record['created_at'] else None,
                    last_login=datetime.fromisoformat(record['last_login']) if record['last_login'] else None
                )
                
                # Update last login
                session.run("""
                    MATCH (u:User {id: $user_id})
                    SET u.last_login = $last_login
                """, user_id=user.id, last_login=datetime.utcnow().isoformat())
                
                return user
                
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            if not self.neo4j_driver:
                return None
                
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (u:User {id: $user_id, is_active: true})
                    RETURN u.id as id, u.email as email, u.password_hash as password_hash,
                           u.first_name as first_name, u.last_name as last_name,
                           u.role as role, u.organization_id as organization_id,
                           u.is_active as is_active, u.created_at as created_at,
                           u.last_login as last_login
                """, user_id=user_id)
                
                record = result.single()
                if not record:
                    return None
                
                return User(
                    id=record['id'],
                    email=record['email'],
                    password_hash=record['password_hash'],
                    first_name=record['first_name'],
                    last_name=record['last_name'],
                    role=UserRole(record['role']),
                    organization_id=record['organization_id'],
                    is_active=record['is_active'],
                    created_at=datetime.fromisoformat(record['created_at']) if record['created_at'] else None,
                    last_login=datetime.fromisoformat(record['last_login']) if record['last_login'] else None
                )
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_users_by_organization(self, org_id: str) -> List[User]:
        """Get all users in an organization"""
        try:
            if not self.neo4j_driver:
                return []
                
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (u:User {organization_id: $org_id, is_active: true})
                    RETURN u.id as id, u.email as email, u.password_hash as password_hash,
                           u.first_name as first_name, u.last_name as last_name,
                           u.role as role, u.organization_id as organization_id,
                           u.is_active as is_active, u.created_at as created_at,
                           u.last_login as last_login
                    ORDER BY u.created_at DESC
                """, org_id=org_id)
                
                users = []
                for record in result:
                    user = User(
                        id=record['id'],
                        email=record['email'],
                        password_hash=record['password_hash'],
                        first_name=record['first_name'],
                        last_name=record['last_name'],
                        role=UserRole(record['role']),
                        organization_id=record['organization_id'],
                        is_active=record['is_active'],
                        created_at=datetime.fromisoformat(record['created_at']) if record['created_at'] else None,
                        last_login=datetime.fromisoformat(record['last_login']) if record['last_login'] else None
                    )
                    users.append(user)
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting users by organization: {e}")
            return []

    def get_organization_by_id(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        try:
            if not self.neo4j_driver:
                return None
                
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (o:Organization {id: $org_id, is_active: true})
                    RETURN o.id as id, o.name as name, o.domain as domain,
                           o.subscription_tier as subscription_tier, o.admin_user_id as admin_user_id,
                           o.settings as settings, o.is_active as is_active,
                           o.created_at as created_at, o.trial_ends_at as trial_ends_at
                """, org_id=org_id)
                
                record = result.single()
                if not record:
                    return None
                
                return Organization(
                    id=record['id'],
                    name=record['name'],
                    domain=record['domain'],
                    subscription_tier=SubscriptionTier(record['subscription_tier']),
                    admin_user_id=record['admin_user_id'],
                    settings=record['settings'],
                    is_active=record['is_active'],
                    created_at=datetime.fromisoformat(record['created_at']) if record['created_at'] else None,
                    trial_ends_at=datetime.fromisoformat(record['trial_ends_at']) if record['trial_ends_at'] else None
                )
                
        except Exception as e:
            logger.error(f"Error getting organization by ID: {e}")
            return None

# Authentication decorators
def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Get auth manager from app context
            auth_manager = current_app.auth_manager
            payload = auth_manager.verify_token(token)
            
            if not payload:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            # Add user info to request context
            request.current_user = payload
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return jsonify({'error': 'Token verification failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        user = request.current_user
        if user['role'] not in ['org_admin', 'super_admin']:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated

def org_admin_required(f):
    """Decorator to require organization admin role"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        user = request.current_user
        if user['role'] != 'org_admin':
            return jsonify({'error': 'Organization admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated

def same_org_required(f):
    """Decorator to ensure user can only access data from their organization"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        user = request.current_user
        # Add organization ID to kwargs for use in the endpoint
        kwargs['current_user_org'] = user['organization_id']
        return f(*args, **kwargs)
    
    return decorated