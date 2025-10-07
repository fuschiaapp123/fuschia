from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import structlog

from app.core.config import settings
from app.models.user import Token, UserCreate, User, UserWithToken
from app.services.postgres_user_service import postgres_user_service
from app.auth.auth import create_access_token, get_current_active_user

router = APIRouter()
logger = structlog.get_logger()


@router.post("/register", response_model=UserWithToken)
async def register(user_create: UserCreate):
    """
    Register a new user and automatically return an access token for immediate login.

    This provides a seamless user experience by eliminating the need for a separate login step.
    """
    try:
        existing_user = await postgres_user_service.get_user_by_email(user_create.email)
        if existing_user:
            logger.warning("Registration failed - email already registered", email=user_create.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user = await postgres_user_service.create_user(user_create)

        # Generate access token for automatic login
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )

        logger.info("User registered successfully with auto-login",
                   user_id=user.id,
                   email=user.email,
                   token_expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        return UserWithToken(
            user=user,
            access_token=access_token,
            token_type="bearer"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like email already registered)
        raise
    except ValueError as e:
        logger.error("Registration validation error", error=str(e), email=user_create.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Registration failed with unexpected error",
                    error=str(e),
                    error_type=type(e).__name__,
                    email=user_create.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await postgres_user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user