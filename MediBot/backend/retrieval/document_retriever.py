from qdrant_client.models import FieldCondition, MatchValue
from backend.core.rbac import get_qdrant_rbac_filter
from backend.db.vector_db import get_vector_store
from backend.retrieval.reranker import rank_documents

from qdrant_client.models import FieldCondition, MatchValue, MatchAny
from typing import Union, List
from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("document_retriever")


def retrieve_documents(query: str, role: str, active_collection: Union[str, List[str]] = "general", top_k: int = 5, candidate_k: int = 20):
    function_name = "retrieve_documents"
    LOGGER.extMethodEntry(function_name, lambda : "Entry")

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

    if candidates:
        raw_log_str = "="*80 + "\n"
        for i, doc in enumerate(candidates):
            source = doc.metadata.get('file_name', 'Unknown')
            collection = doc.metadata.get('collection', 'Unknown')
            preview = doc.page_content.strip().replace('\n', ' ')[:230]
            raw_log_str += f"Raw Chunk {i + 1} | Source: {source} ({collection})\nText: {preview}...\n" + "-"*40 + "\n"

        LOGGER.extDebugTextBlock(function_name, lambda: "Raw Chunks retrieved from Qdrant ->", raw_log_str)
    else:
        LOGGER.extDebugTextBlock(function_name, lambda: "Raw Chunks retrieved from Qdrant ->", "0 chunks found.")

    reranked_docs = rank_documents(query=query, documents=candidates, top_k=top_k)

    if reranked_docs:
        final_log_str = "=" * 80 + "\n"
        for i, doc in enumerate(reranked_docs):
            score = doc.metadata.get('jev_relevance_score', 'N/A')
            preview = doc.page_content.strip().replace('\n', ' ')[:230]
            final_log_str += f"Final Chunk {i + 1} | Jev Score: {score}\nText: {preview}...\n" + "-" * 40 + "\n"

        LOGGER.extDebugTextBlock(function_name, lambda: f"Top {top_k} Reranked Chunks sent to LLM ->", final_log_str)
    else:
        LOGGER.extDebugTextBlock(function_name, lambda: f"Top {top_k} Reranked Chunks sent to LLM ->","Jev rejected all chunks.")

    LOGGER.extMethodExit(function_name, lambda : "Exit")
    return reranked_docs

def format_retrieved_docs(docs: list) -> str:
    """Formats the LangChain documents into a single string for the LLM prompt."""
    function_name = "format_retrieved_docs"
    LOGGER.extMethodEntry(function_name, lambda : "Entry")

    if not docs:
        return ""

    context = "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )

    LOGGER.extDebugAsJson(function_name, lambda: "Formated Chunks for the user query -> ", context)
    LOGGER.extMethodExit(function_name, lambda : "Exit")

    return context