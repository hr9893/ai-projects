from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from backend.core.rbac import get_current_user, ROLE_COLLECTIONS, SQL_ROLE_TABLES
from backend.services.chat_service import process_chat

from backend.utils.logger import ExtensionLoggerFactory

router = APIRouter(prefix="/api/retrieval", tags=["RAG Chat"])
LOGGER = ExtensionLoggerFactory.getLogger("Chat_Router")

@router.get("/vector/{collection}")
async def query_vector_collection(collection: str, current_user: dict = Depends(get_current_user)):
    function_name = "query_vector_collection"
    LOGGER.extMethodEntry(function_name, None, lambda: "Entry")

    role = current_user["role"]
    allowed_collections = ROLE_COLLECTIONS.get(role, [])

    if collection not in allowed_collections:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' does not have access to vector collection '{collection}'"
        )
    LOGGER.extMethodExit(function_name, None, lambda: "Exit")
    return {"message": f"Successfully queried vector collection: {collection}", "user": current_user["username"]}

@router.get("/sql/{table}")
async def query_sql_table(table: str, current_user: dict = Depends(get_current_user)):
    role = current_user["role"]
    allowed_tables = SQL_ROLE_TABLES.get(role, [])

    if table not in allowed_tables:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' does not have access to SQL table '{table}'"
        )
    return {"message": f"Successfully queried SQL table: {table}", "user": current_user["username"]}

class ChatRequest(BaseModel):
    question: str
    collection: str = "general"

@router.post("/query")
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    The main unified endpoint for the frontend.
    Routes between SQL and Vector DBs securely based on intent and RBAC.
    """
    try:
        result = process_chat(
            question=request.question,
            current_user=current_user,
            requested_collection=request.collection
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[ERROR] Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while processing your request.")