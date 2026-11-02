from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from backend.config.configs import (QDRANT_PATH, EMBED_MODEL, QDRANT_COLLECTION)

_vector_store = None

def get_vector_store() -> QdrantVectorStore:
    """Initializes and returns a singleton instance of the Qdrant Hybrid Vector Store."""
    global _vector_store
    if _vector_store is None:
        print("[INIT] Loading Embedding Models and Connecting to Qdrant...")
        dense_embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        sparse_embeddings = FastEmbedSparse(model="Qdrant/bm25")

        _vector_store = QdrantVectorStore.from_existing_collection(
            collection_name=QDRANT_COLLECTION,
            path=str(QDRANT_PATH),
            embedding=dense_embedding,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
        )
        print("[INIT] Qdrant connection established successfully.")

    return _vector_store
