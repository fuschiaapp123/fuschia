from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.models.user import User, UserUpdate
from app.services.user_service import UserService
from app.auth.auth import get_current_active_user

router = APIRouter()


@router.get("/me", response_model=User)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(UserService)
):
    updated_user = await user_service.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(UserService)
):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user