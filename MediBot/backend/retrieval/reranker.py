# backend/retrieval/reranker.py
from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient, TypeSafeError
from langchain_core.documents import Document

JEV_RELEVANCE_THRESHOLD = 0.15

# Notice the backticks around `candidate` and `query`! 
# We define this as a helper function so we can dynamically inject the chunk index.
def get_relevance_question(index: int) -> Noul:
    return Noul(
        # BACKTICKS ARE CRITICAL HERE:
        instructions=f"Does `candidates[{index}]` contain information that helps answer `query`?",
        criteria=NoulCriteria(
            true="Contains specific facts, steps, figures, or definitions that answer the query.",
            false="Only discusses a similar topic or contains generic information.",
        ),
    )

def rank_documents(query: str, documents: list[Document], top_k: int = 5) -> list[Document]:
    """Filter and rerank retrieved chunks using Jev in a single batched API call."""

    candidates = [doc for doc in documents if doc.page_content.strip()]

    if not candidates:
        return []

    try:
        # 1. Build a SINGLE state containing the query and ALL candidates
        state = {
            "query": query,
            "candidates": [doc.page_content for doc in candidates]
        }

        # 2. Build the questions dictionary. One question per candidate, all in parallel!
        questions = {}
        for i in range(len(candidates)):
            questions[str(i)] = get_relevance_question(i)

        # 3. Make ONE single call to Jev
        with TypeSafeClient() as client:
            response = client.system_one(
                state=state,
                questions=questions
            )

        # 4. Extract and filter the scores
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

        # 5. Sort best-to-worst and return top_k
        scored_documents.sort(key=lambda item: item[1], reverse=True)

        print(f"[DEBUG] Jev kept {len(scored_documents)} out of {len(candidates)} candidates.")

        return [doc for doc, score in scored_documents[:top_k]]

    except TypeSafeError as error:
        print(f"[ERROR] Jev reranking failed: {error}")
        return candidates[:top_k]