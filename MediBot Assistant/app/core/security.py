from datetime import datetime, timedelta, timezone

from jose import jwt
from core.constant import Role
from app.config import settings

def create_session_token(username: str, role: Role) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.session_expire_minutes)
    payload = {"sub": username, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.session_secret, algorithm="HS256")


def decode_session_token(token: str) -> dict:
    return jwt.decode(token, settings.session_secret, algorithms=["HS256"])