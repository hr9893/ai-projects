from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient, TypeSafeError
from langchain_core.documents import Document
from backend.utils.logger import ExtensionLoggerFactory

LOGGER = ExtensionLoggerFactory.getLogger("reranker_service")

JEV_RELEVANCE_THRESHOLD = 0.05

def get_relevance_question(index: int) -> Noul:
    return Noul(
        instructions=f"Does `candidates[{index}]` contain information that helps answer `query`?",
        criteria=NoulCriteria(
            true="Contains specific facts, steps, figures, or definitions that answer the query.",
            false="Only discusses a similar topic or contains generic information.",
        ),
    )

def rank_documents(query: str, documents: list[Document], top_k: int = 5) -> list[Document]:
    """Filter and rerank retrieved chunks using Jev in a single batched API call."""
    function_name = "rank_documents"
    LOGGER.extMethodEntry(function_name, lambda : "Entry")

    candidates = [doc for doc in documents if doc.page_content.strip()]

    if not candidates:
        return []

    try:
        state = {
            "query": query,
            "candidates": [doc.page_content for doc in candidates]
        }

        questions = {}
        for i in range(len(candidates)):
            questions[str(i)] = get_relevance_question(i)

        with TypeSafeClient() as client:
            response = client.system_one(
                state=state,
                questions=questions
            )

        scored_documents = []
        for i, doc in enumerate(candidates):
            score = response.answers[str(i)].noul

            if score < JEV_RELEVANCE_THRESHOLD:
                continue

            ranked_doc = doc.model_copy(
                update={
                    "metadata": {
                        **doc.metadata,
                        "jev_relevance_score": score,
                    }
                }
            )

            scored_documents.append((ranked_doc, score))

        scored_documents.sort(key=lambda item: item[1], reverse=True)

        LOGGER.extDebugAsJson(function_name, None, f"Jev kept {len(scored_documents)} out of {len(candidates)} candidates.")

        LOGGER.extMethodEntry(function_name, lambda: "Entry")
        return [doc for doc, score in scored_documents[:top_k]]

    except TypeSafeError as error:
        LOGGER.extError(function_name, lambda: "Jev reranking failed: ", error, str(error))
        return candidates[:top_k]