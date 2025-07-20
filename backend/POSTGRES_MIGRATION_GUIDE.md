# PostgreSQL Migration Guide - User Profiles with RBAC

## Overview
This guide covers the migration of user profiles from Neo4j to PostgreSQL, including the implementation of Role-Based Access Control (RBAC) with new user roles.

## New User Role System

### Role Hierarchy
1. **ADMIN** - Full system access with all administrative privileges
2. **PROCESS_OWNER** - Can create and manage workflows and processes
3. **MANAGER** - Can manage users and view analytics
4. **ANALYST** - Can view analytics and reports
5. **END_USER** - Standard user with basic access to workflows
6. **USER** - Legacy role (deprecated, maps to END_USER)

### Role Permissions Matrix

| Permission | Admin | Process Owner | Manager | Analyst | End User |
|------------|-------|---------------|---------|---------|----------|
| Create Users | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage All Users | ✅ | ❌ | ✅ | ❌ | ❌ |
| View All Users | ✅ | ❌ | ✅ | ❌ | ❌ |
| Create Workflows | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Workflows | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Analytics | ✅ | ✅ | ✅ | ✅ | ❌ |
| Execute Workflows | ✅ | ✅ | ✅ | ✅ | ✅ |
| Update Own Profile | ✅ | ✅ | ✅ | ✅ | ✅ |

## Migration Steps

### 1. Prerequisites

**Install PostgreSQL Dependencies:**
```bash
pip install psycopg2-binary==2.9.9 asyncpg==0.29.0
```

**Setup PostgreSQL Database:**
```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE fuschia_db;
CREATE USER fuschia_user WITH PASSWORD 'fuschia_password';
GRANT ALL PRIVILEGES ON DATABASE fuschia_db TO fuschia_user;
```

### 2. Environment Configuration

**Update `.env` file:**
```env
# Add PostgreSQL configuration
DATABASE_URL=postgresql+asyncpg://fuschia_user:fuschia_password@localhost:5432/fuschia_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fuschia_db
POSTGRES_USER=fuschia_user
POSTGRES_PASSWORD=fuschia_password
```

### 3. Database Migration

**Run the migration script:**
```bash
cd /Users/sanjay/Lab/Fuschia-alfa/backend
python migrate_users_to_postgres.py
```

**Migration Process:**
1. Tests PostgreSQL connectivity
2. Initializes PostgreSQL database schema
3. Fetches all users from Neo4j
4. Maps legacy roles to new role system
5. Migrates users to PostgreSQL
6. Verifies migration success
7. Shows role distribution

### 4. Role Mapping

Legacy Neo4j roles are automatically mapped:
- `admin` → `ADMIN`
- `manager` → `MANAGER`
- `analyst` → `ANALYST`
- `user` → `END_USER`
- `process_owner` → `PROCESS_OWNER`
- Unknown roles → `END_USER` (default)

## API Endpoints

### Authentication Endpoints
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### User Management Endpoints
- `GET /api/v1/users/` - Get all users (Admin/Manager only)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `POST /api/v1/users/` - Create user (Admin only)
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Deactivate user (Admin only)
- `GET /api/v1/users/by-role/{role}` - Get users by role (Admin/Manager only)
- `GET /api/v1/users/role-counts` - Get user statistics (Admin/Manager only)
- `GET /api/v1/users/roles/available` - Get available roles

### Self-Service Endpoints
- `GET /api/v1/users/me` - Get own profile
- `PUT /api/v1/users/me` - Update own profile

## Role-Based Access Control Implementation

### Permission Decorators
```python
# Require admin role
@router.post("/admin-only")
async def admin_endpoint(current_user: User = Depends(require_admin)):
    pass

# Require admin or manager role
@router.get("/management")
async def management_endpoint(current_user: User = Depends(require_admin_or_manager)):
    pass

# Require process owner or above
@router.post("/workflows")
async def workflow_endpoint(current_user: User = Depends(require_process_owner_or_above)):
    pass
```

### Permission Checking
```python
# Check if user has specific permissions
has_permission = await postgres_user_service.user_has_permission(
    user_id, 
    [UserRole.ADMIN, UserRole.PROCESS_OWNER]
)
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    role user_role NOT NULL DEFAULT 'end_user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    hashed_password VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TYPE user_role AS ENUM (
    'admin',
    'process_owner', 
    'manager',
    'analyst',
    'end_user',
    'user'
);
```

### Indexes
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
```

## Testing the Migration

### 1. Test Database Connection
```bash
python -c "
import asyncio
from app.db.postgres import test_db_connection
asyncio.run(test_db_connection())
"
```

### 2. Test User Creation
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "full_name": "Admin User",
    "password": "securepassword123",
    "role": "admin"
  }'
```

### 3. Test Authentication
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=securepassword123"
```

### 4. Test Role-Based Access
```bash
# Get users (requires admin/manager role)
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get role counts
curl -X GET "http://localhost:8000/api/v1/users/role-counts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Performance Considerations

### Connection Pooling
- Pool size: 20 connections
- Max overflow: 30 connections
- Connection recycling: 1 hour
- Pre-ping enabled for connection health

### Query Optimization
- Indexed fields: email, role, is_active, created_at
- Efficient pagination with LIMIT/OFFSET
- Role-based filtering at database level

### Monitoring
- Structured logging with user actions
- Database performance metrics
- Authentication success/failure tracking

## Security Features

### Password Security
- BCrypt hashing with salt
- Minimum password length enforcement
- Password verification timing protection

### Access Control
- JWT token-based authentication
- Role-based permission checking
- Session management
- Account deactivation (soft delete)

### Audit Trail
- User creation/modification logging
- Role change tracking
- Authentication attempt logging
- Permission check logging

## Troubleshooting

### Common Issues

**1. Connection Error**
```
ERROR: Database connection failed
```
**Solution:** Check PostgreSQL service, credentials, and network connectivity

**2. Migration Failed**
```
ERROR: User creation failed - email already exists
```
**Solution:** Check for duplicate emails in Neo4j, clean data before migration

**3. Permission Denied**
```
HTTP 403: Not enough permissions
```
**Solution:** Verify user role and required permissions for the endpoint

**4. Role Mapping Issues**
```
WARNING: Unknown role mapped to end_user
```
**Solution:** Update role mapping in migration script for custom roles

### Database Maintenance

**Backup:**
```bash
pg_dump -U fuschia_user -h localhost fuschia_db > fuschia_backup.sql
```

**Restore:**
```bash
psql -U fuschia_user -h localhost fuschia_db < fuschia_backup.sql
```

**Monitor Performance:**
```sql
-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('users'));

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE schemaname = 'public';
```

## Rollback Plan

If issues occur, you can rollback by:

1. **Revert authentication service:**
   ```python
   # In app/auth/auth.py, change back to:
   from app.services.user_service import UserService
   ```

2. **Update API endpoints:**
   ```python
   # In app/api/endpoints/auth.py and users.py
   # Change imports back to Neo4j service
   ```

3. **Restore Neo4j as primary:**
   - Keep PostgreSQL for reference
   - Switch authentication back to Neo4j
   - Migrate any new users back to Neo4j if needed

## Benefits of PostgreSQL Migration

1. **Better Performance:** Optimized queries and indexing
2. **ACID Compliance:** Guaranteed data consistency
3. **Mature Ecosystem:** Rich tooling and monitoring
4. **Scalability:** Better handling of concurrent users
5. **Role-Based Security:** Fine-grained access control
6. **Standard SQL:** Easier maintenance and optimization
7. **Backup & Recovery:** Enterprise-grade data protection

This migration enhances the platform's user management capabilities while providing a solid foundation for role-based access control and future scalability.