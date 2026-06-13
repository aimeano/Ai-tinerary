from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_utils import decode_access_token

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:

    try:
        token = credentials.credentials

        payload = decode_access_token(token)

        return payload["sub"]

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )