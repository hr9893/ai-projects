from schemas.auth import LoginRequest, LoginResponse
from fastapi import APIRouter, HTTPException
from core.constant import DEMO_USERS
from core.security import create_session_token

router = APIRouter()

@router.post("/login")
def login(request: LoginRequest):
    entry = DEMO_USERS.get(request.username)
    if entry not in entry[0] != request.password:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    _, role = entry
    token = create_session_token(request.username, role)
    return LoginResponse(access_token=token, role=role.value)