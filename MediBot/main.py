from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from backend.app.router import classify_query, is_drug_related
from backend.app.rcba import can_use_sql_rag, access_roles_for_collection
from backend.app.sql_rag import answer_sql_query
from backend.app.rcba import format_doc_answer
from backend.app.search import get_existing_vector_store, retrieve_document
from backend.app.config import QDRANT_PATH

app = FastAPI()

vector_store = get_existing_vector_store(QDRANT_PATH)

class QueryRequest(BaseModel):
    question: str
    role: str


class QueryResponse(BaseModel):
    answer: str
    route: str


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):

    # --- Step 1: hard override for drug-related questions ---
    # Always vector search + LLM synthesis, never SQL, regardless of
    # what the router would otherwise decide.
    if is_drug_related(request.question):
        if not access_roles_for_collection(request.role, "pharmacy"):
            return QueryResponse(
                answer="Your role does not have access to drug or medication information.",
                route="rag-drug-denied",
            )

        docs = retrieve_document(vector_store, request.question, request.role)
        answer = format_doc_answer(request.question, docs)
        return QueryResponse(answer=answer, route="rag-drug")

    # --- Step 2: normal routing for everything else ---
    classification = classify_query(request.question)
    route = classification["route"]

    if route == "sql":
        if not can_use_sql_rag(request.role):
            return QueryResponse(answer="Your role does not have access to this data.", route=route)
        answer = answer_sql_query(request.question, request.role)

    elif route == "rag":
        docs = retrieve_document(vector_store, request.question, request.role)
        answer = format_doc_answer(request.question, docs)

    else:  # "both"
        sql_answer = (
            answer_sql_query(request.question, request.role)
            if can_use_sql_rag(request.role)
            else None
        )
        docs = retrieve_document(vector_store, request.question, request.role)
        doc_answer = format_doc_answer(request.question, docs)
        answer = merge_answers(request.question, sql_answer, doc_answer)

    return QueryResponse(answer=answer, route=route)


def merge_answers(question: str, sql_answer: str | None, doc_answer: str | None) -> str:
    parts = [p for p in [sql_answer, doc_answer] if p]
    if not parts:
        return "I couldn't find relevant information for that question."
    if len(parts) == 1:
        return parts[0]
    return "\n\n".join(parts)