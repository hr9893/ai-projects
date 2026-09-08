from pathlib import Path
import os

# ===== Paths =====
BASE_DIR = Path(__file__).resolve().parents[2]   # .../medibot
DATA_DIR = BASE_DIR / "data"

DOC_DIRS = {
    "general": DATA_DIR / "general",
    "clinical": DATA_DIR / "clinical",
    "nursing": DATA_DIR / "nursing",
    "billing": DATA_DIR / "billing",
    "equipment": DATA_DIR / "equipment",
}

SQLITE_PATH = DATA_DIR / "mediassist.db"

# ===== Models =====
GROQ_MODEL = "openai/gpt-oss-20b"  # your example
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# ===== Qdrant =====
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # None for local
QDRANT_COLLECTION = "medibot_hybrid"

# ===== Auth (for later FastAPI) =====
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGO = "HS256"

MEDIASSIST_DB_PATH = "backend/data/db/mediassist.db"

QDRANT_PATH = "backend\qdrant_db"

GROQ_API_KEY = "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"
