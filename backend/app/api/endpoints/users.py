from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from app.models.user import User, UserCreate, UserUpdate, UserRole, PasswordChange, AdminPasswordReset
from app.services.postgres_user_service import postgres_user_service
from app.auth.auth import get_current_active_user

router = APIRouter()


def require_admin_or_manager(current_user: User = Depends(get_current_active_user)):
    """Dependency to require admin or manager role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin or Manager role required."
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


@router.get("/me", response_model=User)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    # Users cannot change their own role unless they're admin
    if (current_user.role != UserRole.ADMIN and user_update.role is not None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    try:
        updated_user = await postgres_user_service.update_user(current_user.id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.get("/", response_model=List[User])
async def get_users(
    active_only: bool = Query(True, description="Return only active users"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    current_user: User = Depends(require_admin_or_manager)
):
    """Get all users (Admin/Manager only)"""
    try:
        users = await postgres_user_service.get_all_users(
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/by-role/{role}", response_model=List[User])
async def get_users_by_role(
    role: UserRole,
    active_only: bool = Query(True, description="Return only active users"),
    current_user: User = Depends(require_admin_or_manager)
):
    """Get users by role (Admin/Manager only)"""
    try:
        users = await postgres_user_service.get_users_by_role(role, active_only)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users by role: {str(e)}"
        )


@router.get("/role-counts")
async def get_user_role_counts(
    current_user: User = Depends(require_admin_or_manager)
):
    """Get count of users by role (Admin/Manager only)"""
    try:
        role_counts = await postgres_user_service.get_user_count_by_role()
        return {
            "role_counts": role_counts,
            "total_users": sum(role_counts.values())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve role counts: {str(e)}"
        )


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID (users can view their own profile, admins/managers can view anyone)"""
    # Users can only view their own profile unless they're admin/manager
    if (current_user.id != user_id and 
        current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this user"
        )
    
    user = await postgres_user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/", response_model=User)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(require_admin)
):
    """Create a new user (Admin only)"""
    try:
        user = await postgres_user_service.create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update user (users can update themselves, admins can update anyone)"""
    # Users can only update their own profile unless they're admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )
    
    # Non-admins cannot change their own role
    if (current_user.id == user_id and 
        current_user.role != UserRole.ADMIN and 
        user_update.role is not None):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    try:
        updated_user = await postgres_user_service.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_admin)
):
    """Deactivate a user (Admin only)"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    success = await postgres_user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deactivated successfully"}


@router.get("/roles/available")
async def get_available_roles(
    current_user: User = Depends(get_current_active_user)
):
    """Get all available user roles"""
    roles = [
        {
            "value": role.value,
            "name": role.value.replace("_", " ").title(),
            "description": _get_role_description(role)
        }
        for role in UserRole
    ]
    
    return {"roles": roles}


@router.post("/me/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """Change current user's password"""
    # Validate that new password and confirm password match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match"
        )
    
    # Prevent using the same password
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    try:
        success = await postgres_user_service.change_password(
            current_user.id, 
            password_data.current_password, 
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password. Please check your current password."
            )
        
        return {"message": "Password changed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )


@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    password_data: AdminPasswordReset,
    current_user: User = Depends(require_admin_or_manager)
):
    """Admin/Manager reset password for any user"""
    # Only admins can reset other admin passwords
    if current_user.role != UserRole.ADMIN:
        target_user = await postgres_user_service.get_user_by_id(user_id)
        if target_user and target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can reset admin passwords"
            )

    # Validate that new password and confirm password match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match"
        )

    try:
        # Check if target user exists
        target_user = await postgres_user_service.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Reset the password
        success = await postgres_user_service.admin_reset_password(
            user_id,
            password_data.new_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reset password"
            )

        return {
            "message": f"Password reset successfully for user {target_user.email}",
            "user_email": target_user.email
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting password"
        )


def _get_role_description(role: UserRole) -> str:
    """Get description for each role"""
    descriptions = {
        UserRole.ADMIN: "Full system access with all administrative privileges",
        UserRole.PROCESS_OWNER: "Can create and manage workflows and processes",
        UserRole.MANAGER: "Can manage users and view analytics",
        UserRole.ANALYST: "Can view analytics and reports",
        UserRole.END_USER: "Standard user with basic access to workflows",
        UserRole.USER: "Legacy user role (deprecated)"
    }
    return descriptions.get(role, "Standard user role")