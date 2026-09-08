from typing import List, Tuple

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from pathlib import Path
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse

from backend.app.ingest import DENSE_MODEL, SPARSE_MODEL, COLLECTION_NAME
from backend.app.rcba import qdrant_rbac_filter

from backend.app.config import EMBED_MODEL, QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

_embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

_vectorstore = Qdrant(
    client=None,  # will be created from URL
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    collection_name=QDRANT_COLLECTION,
    embeddings=_embeddings,
)

def search_with_rbac(query : str, role: str, k : int=5,)-> List[Tuple[Document, float]]:
    """Search with the user assigned roles"""
    flt = qdrant_rbac_filter(role)

    query_embedd = _vectorstore.similarity(query, k=k, filter=flt)
    return query_embedd

def create_embeddings_and_store(documents: list[Document],qdrant_path: Path,) -> QdrantVectorStore:

    if not documents:
        raise ValueError("No documents found for embedding.")

    dense_embedding = HuggingFaceEmbeddings(model_name=DENSE_MODEL,)

    sparse_embedding = FastEmbedSparse(model=SPARSE_MODEL,)

    vector_store = QdrantVectorStore.from_documents(
        documents=documents,
        embedding=dense_embedding,
        sparse_embedding=sparse_embedding,
        path=str(qdrant_path),
        collection_name=COLLECTION_NAME,
        retrieval_mode=RetrievalMode.HYBRID,
    )

    print(f"Stored {len(documents)} documents in Qdrant",flush=True,)

    return vector_store