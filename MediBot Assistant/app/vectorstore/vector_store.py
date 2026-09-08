from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from app.ingestion.ingest_pipeline import run_full_ingestion



doc = run_full_ingestion()


