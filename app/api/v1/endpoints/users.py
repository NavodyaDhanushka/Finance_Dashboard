from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import require_permission, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users [Admin only]",
    dependencies=[Depends(require_permission("users:read"))],
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, users = user_service.list_users(db, skip=skip, limit=page_size)
    return UserListResponse(total=total, items=users)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a new user [Admin only]",
    dependencies=[Depends(require_permission("users:create"))],
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, payload)


@router.get("/me", response_model=UserResponse, summary="Get the currently authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID [Admin only]",
    dependencies=[Depends(require_permission("users:read"))],
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user_by_id(db, user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user [Admin only]",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:update")),
):
    return user_service.update_user(db, user_id, payload, acting_user=current_user)


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete a user [Admin only]",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users:delete")),
):
    user_service.delete_user(db, user_id, acting_user=current_user)
