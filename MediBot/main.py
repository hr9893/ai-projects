import os
import shutil
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from backend.app.router import classify_query, is_drug_related
from backend.app.rcba import allowed_collections, can_use_sql_rag
from backend.app.sql_rag import answer_sql_query
from backend.app.rcba import format_doc_answer
from backend.app.search import get_existing_vector_store, retrieve_document
from backend.app.config import QDRANT_PATH

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
frontend_process: subprocess.Popen | None = None


def start_frontend() -> None:
    global frontend_process

    if os.getenv("MEDIBOT_AUTOSTART_FRONTEND", "true").lower() != "true":
        return

    if not (FRONTEND_DIR / "package.json").exists():
        print(f"Frontend was not started: {FRONTEND_DIR} does not contain package.json")
        return

    node_command = shutil.which("node")
    next_cli = FRONTEND_DIR / "node_modules" / "next" / "dist" / "bin" / "next"
    if node_command is None:
        print("Frontend was not started: node was not found on PATH")
        return
    if not next_cli.exists():
        print(f"Frontend was not started: {next_cli} does not exist; run npm install in frontend")
        return

    try:
        frontend_process = subprocess.Popen(
            [node_command, str(next_cli), "dev"],
            cwd=FRONTEND_DIR,
        )
        print("Frontend started at http://localhost:3000")
    except FileNotFoundError:
        print("Frontend was not started: npm was not found on PATH")
    except OSError as error:
        print(f"Frontend was not started: {error}")


def stop_frontend() -> None:
    global frontend_process

    if frontend_process is None or frontend_process.poll() is not None:
        return

    frontend_process.terminate()
    try:
        frontend_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        frontend_process.kill()
        frontend_process.wait()
    frontend_process = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_frontend()
    yield
    stop_frontend()


app = FastAPI(lifespan=lifespan)

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
        if "pharmacy" not in allowed_collections(request.role):
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