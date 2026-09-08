from pydantic_settings import BaseSettings
import sys
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse


class Settings(BaseSettings):

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    QDRANT_DB_PATH = PROJECT_ROOT / "qdrant_db"
    COLLECTION_NAME = "medibot_hybrid"

    # Embeddings initialization
    dense_embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    sparse_embedding = FastEmbedSparse(model_name="Qdrant/bm25")

settings = Settings()