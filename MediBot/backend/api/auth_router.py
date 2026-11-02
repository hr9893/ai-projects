from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.core.security import create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.db.mockdb import get_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Validates user credentials and returns a JWT token.
    """
    user = get_user(form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username")

    is_valid_password = False

    if user.get("password") == form_data.password:
        is_valid_password = True

    elif "password" in user:
        try:
            is_valid_password = verify_password(form_data.password, user["password"])
        except Exception:
            pass

    if not is_valid_password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}