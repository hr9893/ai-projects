from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import (FastEmbedSparse,QdrantVectorStore,RetrievalMode,)
from backend.app.config import (GROQ_MODEL,EMBED_MODEL,QDRANT_COLLECTION)
from backend.app.rcba import (ROLE_COLLECTIONS,qdrant_rbac_filter)
from backend.app.reranker import rank_document


def get_existing_vector_store(qdrant_path: Path, ) -> QdrantVectorStore:
    dense_embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    sparse_embeddings = FastEmbedSparse(model="Qdrant/bm25",)

    result = QdrantVectorStore.from_existing_collection(collection_name=QDRANT_COLLECTION,
                                                        path=str(qdrant_path),
                                                        embedding=dense_embedding,
                                                        sparse_embedding=sparse_embeddings,
                                                        retrieval_mode=RetrievalMode.HYBRID,
                                                        )
    return result


def retrieve_document(vector_store: QdrantVectorStore, query: str, role: str,
                      top_k=5,
                      candidate_k: int = 20,):
    user_role = role.lower()
    rbac_filter = qdrant_rbac_filter(user_role)

    candidates = vector_store.similarity_search(query=query,
                                                k = candidate_k,
                                                filter=rbac_filter,)

    reranked = rank_document(query=query,documents=candidates, top_k= top_k)

    return reranked
