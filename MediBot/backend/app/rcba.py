from langchain_core.documents import Document
from qdrant_client.models import Filter, FieldCondition, MatchValue
from backend.app.llm import LLMClient


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

DOC_SYSTEM_PROMPT = """You are a MediAssist hospital knowledge assistant.
Answer the user's question using ONLY the provided context excerpts below.
If the context doesn't contain enough information to answer confidently,
say so plainly rather than guessing.
Be concise and specific. Mention which source file(s) the answer came from."""

def allowed_collections(role : str)-> list[str]:
    role = role.lower()

    if role not in ROLE_COLLECTIONS:
        raise PermissionError(f"Unknown role: {role}")

    return ROLE_COLLECTIONS[role]

def access_roles_for_collection(collection :str)-> list[str]:
    """which role can see a given collection"""
    result = []

    for role, collections in ROLE_COLLECTIONS.items():
        if collection in collections:
            result.append(role)

    return result


def qdrant_rbac_filter(role: str) -> Filter:
    """Qdrant filter used on every search query. It ensures only chunks whose
    payload.access_roles contains the user role are returned."""

    role = role.lower()

    if role not in ROLE_COLLECTIONS:
        raise PermissionError(f"Unknown role: {role}")

    return Filter(
        must=[
            FieldCondition(
                key="metadata.access_role",
                match=MatchValue(value=role),
            )
        ]
    )

def allowed_sql_tables(role: str) -> list[str]:
    role = role.lower()
    if role not in SQL_ROLE_TABLES:
        raise PermissionError(f"Unknown role: {role}")
    return SQL_ROLE_TABLES[role]


def can_use_sql_rag(role: str) -> bool:
    return len(allowed_sql_tables(role)) > 0

def format_doc_answer(question: str, docs: list[Document]) -> str:
    if not docs:
        return "I couldn't find relevant information for that question."

    context = "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )

    prompt = f"""{DOC_SYSTEM_PROMPT}

Context:
{context}

Question: {question}

Answer:"""

    return LLMClient.get_instance().complete(prompt, temperature=0.2)
