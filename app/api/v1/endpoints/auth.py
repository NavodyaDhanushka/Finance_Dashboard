from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserResponse
from app.services.user_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Login and receive JWT token")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token, user = authenticate_user(db, payload.email, payload.password)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
