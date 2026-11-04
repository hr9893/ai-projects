from fastapi import HTTPException, status

from backend.router.jev_router import classify_query

from backend.core.rbac import get_allowed_collections, get_allowed_sql_tables
from backend.retrieval.document_retriever import retrieve_documents
from backend.retrieval.formater import format_doc_answer
from backend.services.synthesizer import generate_rag_answer
from backend.sql_rag.sql_agent import answer_sql_query

from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("Chat_Service")

def process_chat(question: str, current_user: dict, requested_collection: str) -> dict:
    function_name = "process_chat"
    LOGGER.extMethodEntry(function_name, None, lambda: "Entry")

    user_role = current_user["role"]

    classification = classify_query(question)
    route = classification["route"]
    is_drug_related = classification["drug_related"]

    LOGGER.extDebugAsJson(function_name, lambda: f"[DEBUG] User: {user_role} | Route: {route} | Drug Related: {is_drug_related} | Confidence: {classification['confidence']}")

    rag_answer = ""
    sql_answer = ""

    allowed_collections = get_allowed_collections(user_role)

    if is_drug_related:
        if "pharmacy" not in allowed_collections:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="RBAC DENIED: Your role does not have access to drug or medication information."
            )

        print("[DEBUG] Hard Override: Forcing retrieval to 'pharmacy' collection.")
        docs = retrieve_documents(
            query=question,
            role=user_role,
            active_collection="pharmacy",
            top_k=5
        )
        context = format_doc_answer(docs)
        answer = generate_rag_answer(question, context)

        return {
            "answer": answer,
            "route": "retrieval-drug"
        }

    if route in ["rag", "both"]:
        if requested_collection != "All collections" and requested_collection not in allowed_collections:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"RBAC DENIED: Cannot query '{requested_collection}' documents."
            )

        LOGGER.extDebugAsJson(function_name, lambda: "Searching across all authorized collections: ", allowed_collections)
        docs = retrieve_documents(
            query=question,
            role=user_role,
            active_collection=allowed_collections,
            top_k=5
        )

        context = format_doc_answer(docs)
        rag_answer = generate_rag_answer(question, context)

    if route in ["sql", "both"]:
        allowed_tables = get_allowed_sql_tables(user_role)
        if not allowed_tables:
            # If they were strictly routed to SQL but have no access, block them.
            if route == "sql":
                raise HTTPException(status_code=403, detail="RBAC DENIED: No SQL access.")
            else:
                # If 'both', just skip the SQL part silently so they still get the RAG answer.
                sql_answer = ""
        else:
            # TODO: We will plug your sql_rag.py answer_sql_query here next!
            sql_answer = answer_sql_query(question, user_role)

    # --- Step 5: Merge Answers ---
    if route == "both" and sql_answer:
        final_answer = f"**Document Data:**\n{rag_answer}\n\n**Database Data:**\n{sql_answer}"
    elif route == "sql":
        final_answer = sql_answer
    else:
        final_answer = rag_answer

    return {
        "answer": final_answer,
        "route": route
    }