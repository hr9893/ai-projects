from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

from backend.core.security import oauth2_scheme, SECRET_KEY, ALGORITHM
from backend.db.mockdb import get_user

ROLE_COLLECTIONS = {
    "doctor":           ["general", "clinical", "nursing", "pharmacy"],
    "nurse":            ["general", "nursing", "pharmacy"],
    "billing_executive":["general", "billing"],
    "technician":       ["general", "equipment"],
    "admin":            ["general", "clinical", "nursing", "billing", "equipment", "pharmacy"],
}

SQL_ROLE_TABLES = {
    "admin":             ["claims", "maintenance_tickets"],
    "doctor":            ["claims"],
    "nurse":             [],
    "billing_executive": ["claims"],
    "technician":        ["maintenance_tickets"],
}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the JWT token, extracts the user, and ensures they exist.
    Injected into all protected API endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception

    return user

def get_allowed_collections(role: str) -> list[str]:
    """Returns the list of vector collections a role can query."""
    role = role.lower()
    if role not in ROLE_COLLECTIONS:
        raise PermissionError(f"Unknown role: {role}")
    return ROLE_COLLECTIONS[role]

def get_qdrant_rbac_filter(role: str) -> Filter:
    """
    Qdrant filter used on EVERY search query.
    It ensures only chunks whose payload.metadata.access_role 
    contains the user role are returned.
    """
    role = role.lower()
    if role not in ROLE_COLLECTIONS:
        raise PermissionError(f"Unknown role: {role}")

    return Filter(
        must=[
            FieldCondition(
                key="metadata.access_role",
                match=MatchAny(any=[role]),
            )
        ]
    )

def get_allowed_sql_tables(role: str) -> list[str]:
    """
    Returns the strict list of SQL tables this role can view.
    Used to scope the LangChain SQLDatabase connection.
    """
    role = role.lower()
    if role not in SQL_ROLE_TABLES:
        raise PermissionError(f"Unknown role: {role}")
    return SQL_ROLE_TABLES[role]

def can_use_sql_rag(role: str) -> bool:
    """Quick check to see if we should even bother routing to SQL."""
    return len(get_allowed_sql_tables(role)) > 0