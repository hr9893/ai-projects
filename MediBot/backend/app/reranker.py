from backend.app.config import RERANKER_MODEL
from sentence_transformers import CrossEncoder

_reranker = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker

def rank_document(query : str, documents : list, top_k: int = 5)-> list:
    """
    Re-score retrieved LangChain Documents against the query using a
    cross-encoder, and return the top_k re-ordered by relevance.
    """

    reranker = get_reranker()

    pairs = [(query, doc.page_content) for doc in documents]

    score = reranker.predict(pairs)

    score_doc = list(zip(documents, score))
    score_doc.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, score in score_doc[:top_k]]