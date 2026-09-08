from fastapi import Header, HTTPException

from core.constant import Role
from core.security import decode_session_token

def get_current_role(authorization: str = Header(...)) -> Role:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_session_token(token)
        return Role(payload["role"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")