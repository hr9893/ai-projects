from qdrant_client.models import FieldCondition, MatchValue
from backend.core.rbac import get_qdrant_rbac_filter
from backend.db.vector_db import get_vector_store
from backend.retrieval.reranker import rank_documents

from qdrant_client.models import FieldCondition, MatchValue, MatchAny
from typing import Union, List


def retrieve_documents(query: str, role: str, active_collection: Union[str, List[str]] = "general", top_k: int = 5, candidate_k: int = 20):
    vector_store = get_vector_store()
    security_filter = get_qdrant_rbac_filter(role)

    if isinstance(active_collection, list):
        ui_filter = FieldCondition(
            key="metadata.collection",
            match=MatchAny(any=active_collection)
        )
        security_filter.must.append(ui_filter)
    elif active_collection and active_collection not in ["All collections", "general"]:
        ui_filter = FieldCondition(
            key="metadata.collection",
            match=MatchValue(value=active_collection)
        )
        security_filter.must.append(ui_filter)

    candidates = vector_store.similarity_search(query=query, k=candidate_k, filter=security_filter)
    reranked_docs = rank_documents(query=query, documents=candidates, top_k=top_k)

    return reranked_docs

def format_retrieved_docs(docs: list) -> str:
    """Formats the LangChain documents into a single string for the LLM prompt."""
    if not docs:
        return ""

    context = "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )
    return context