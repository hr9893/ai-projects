import re
from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from backend.core.llm_config import generate_completion
from backend.core.rbac import get_allowed_sql_tables
from langchain_groq import ChatGroq
from backend.config.configs import (MEDIASSIST_DB_PATH, SQL_MODEL)
import os

SYSTEM_PROMPT = """You are a MediAssist hospital operations assistant.
Given a user question and the SQL query result from our database,
provide a clear, concise natural language answer.
Be specific with numbers, dates, and names present in the data.
Do not mention SQL, tables, or databases in your answer."""

def get_scoped_db(allowed_tables: list[str]) -> SQLDatabase:
    """Build a SQLDatabase handle restricted to only the allowed tables."""
    return SQLDatabase.from_uri(
        f"sqlite:///{MEDIASSIST_DB_PATH}",
        include_tables=allowed_tables,
    )

def clean_sql(raw: str) -> str:
    """Strip markdown fences and any preamble, leaving only the SQL statement."""
    raw = re.sub(r"```(?:sql)?", "", raw).strip("`").strip()
    if "SQLQuery:" in raw:
        raw = raw.split("SQLQuery:")[-1].strip()
    return raw

def is_safe_sql(sql: str, allowed_tables: list[str]) -> bool:
    """Defense-in-depth check BEFORE execution."""
    normalized = sql.strip().lower().rstrip(";").strip()
    if not normalized.startswith("select"):
        return False
    if ";" in normalized:
        return False

    forbidden = ["insert", "update", "delete", "drop", "alter",
                 "truncate", "grant", "revoke", "create", "--", "/*", "attach"]

    for keyword in forbidden:
        if keyword in ("--", "/*"):
            if keyword in normalized:
                return False
        elif re.search(rf"\b{re.escape(keyword)}\b", normalized):
            return False

    referenced_tables = re.findall(
        r"(?:\bfrom|\bjoin)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        r"(?!\s*\()", normalized,
    )

    if not referenced_tables:
        return False

    if any(t not in [a.lower() for a in allowed_tables] for t in referenced_tables):
        return False

    return True

def answer_sql_query(user_query: str, role: str) -> str:
    """Full pipeline: text -> SQL -> validate -> execute -> natural language."""
    allowed_tables = get_allowed_sql_tables(role)
    if not allowed_tables:
        return "Your role does not have access to structured hospital data."

    try:
        db = get_scoped_db(allowed_tables)
    except Exception as e:
        print(f"[ERROR] Failed to connect to SQLite DB at {MEDIASSIST_DB_PATH}: {e}")
        return "I am currently unable to connect to the hospital database."

    # We use LangChain's specific ChatGroq here because create_sql_query_chain
    # strictly requires a LangChain BaseChatModel object, not a raw string.
    # (Ensure GROQ_API_KEY is in your environment)
    llm = ChatGroq(model=SQL_MODEL, temperature=0)

    try:
        sql_query_chain = create_sql_query_chain(llm, db)
        raw_sql = sql_query_chain.invoke({"question": user_query})

        sql = clean_sql(raw_sql)
        print(f"[DEBUG] Generated SQL: {sql}")

        if not is_safe_sql(sql, allowed_tables):
            return "Sorry, I couldn't safely process that data request."

        # Execute against SQLite
        result = db.run(sql)

        # Pass the raw result to LiteLLM for natural language synthesis
        answer_prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {user_query}\nSQL Result: {result}\n\nAnswer:"

        final_answer = generate_completion(
            prompt=answer_prompt,
            model=SQL_MODEL,
            temperature=0.1
        )

        return final_answer

    except Exception as e:
        print(f"[ERROR] SQL Agent failed: {e}")
        return "An error occurred while analyzing the database."
