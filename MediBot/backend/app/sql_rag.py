import re

from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate
from backend.app.llm import LLMClient

from backend.app.config import MEDIASSIST_DB_PATH, GROQ_MODEL
from backend.app.rcba import allowed_sql_tables

SYSTEM_PROMPT = """You are a MediAssist hospital operations assistant.
Given a user question and the SQL query result from our database,
provide a clear, concise natural language answer.
Be specific with numbers, dates, and names present in the data.
Do not mention SQL, tables, or databases in your answer."""

def get_scoped_db(allowed_tables: list[str]) -> SQLDatabase:
    """
    Build a SQLDatabase handle restricted to only the tables this
    role is allowed to see. include_tables is enforced by langchain
    itself when building schema context for the LLM — tables not
    listed here are invisible to the query-generation step.
    """
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

def normalize_sql_for_sqlite(sql: str) -> str:
    """Convert common non-SQLite date expressions emitted by SQL models."""
    sql = re.sub(
        r"EXTRACT\s*\(\s*YEAR\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        lambda match: "CAST(strftime('%Y', {}) AS INTEGER)".format(match.group(1)),
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"\bYEAR\s*\(\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\)",
        lambda match: "CAST(strftime('%Y', {}) AS INTEGER)".format(match.group(1)),
        sql,
        flags=re.IGNORECASE,
    )
    return sql

def is_safe_sql(sql: str, allowed_tables: list[str]) -> bool:
    """Defense-in-depth check BEFORE execution — never trust LLM output alone."""
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

    # Only FROM/JOIN clauses followed by a table identifier are considered.
    # Expressions such as EXTRACT(YEAR FROM submitted_date) are normalized
    # before this check and must not be treated as table references.
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
    allowed_tables = allowed_sql_tables(role)

    if not allowed_tables:
        return "Your role does not have access to this data."

    db = get_scoped_db(allowed_tables)
    llm = LLMClient.get_instance().chat_model

    sql_query_chain = create_sql_query_chain(llm, db)
    raw_sql = sql_query_chain.invoke({"question": user_query})
    sql = normalize_sql_for_sqlite(clean_sql(raw_sql))
    print(f"[DEBUG] Generated SQL: {sql}")

    if not is_safe_sql(sql, allowed_tables):
        return "Sorry, I couldn't safely process that request."

    result = db.run(sql)

    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "Question: {question}\nSQL Result: {result}\n\nAnswer:"),
    ])
    response_chain = answer_prompt | llm
    response = response_chain.invoke({"question": user_query, "result": result})

    return response.content