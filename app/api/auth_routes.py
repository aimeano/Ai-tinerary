from fastapi import APIRouter, HTTPException

from app.db.database import SessionLocal
from app.db.auth_repository import (
    signup_user,
    login_user,
)
from app.auth.jwt_utils import create_access_token
from app.api.schemas import (
    SignupRequest,
    LoginRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(payload: SignupRequest):

    db = SessionLocal()

    try:
        user = signup_user(
            db,
            email=payload.email,
            password=payload.password,
            name=payload.name,
        )

        token = create_access_token(user.user_id)

        return {
            "access_token": token,
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    finally:
        db.close()

@router.post("/login")
def login(payload: LoginRequest):

    db = SessionLocal()

    try:
        user = login_user(
            db,
            email=payload.email,
            password=payload.password,
        )

        token = create_access_token(user.user_id)

        return {
            "access_token": token,
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

    finally:
        db.close()