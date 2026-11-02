# backend/core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Force load the .env file so os.getenv can see it
load_dotenv()

# =====================================================================
# ENVIRONMENT INJECTION FOR SDKS (LiteLLM / TypeSafe)
# =====================================================================
# Extract the keys from the .env file
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Push them back into os.environ so the external SDKs can find them natively
if TYPESAFE_API_KEY:
    os.environ["TYPESAFE_API_KEY"] = TYPESAFE_API_KEY
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# =====================================================================
# PATHS
# =====================================================================
BASE_DIR = Path(__file__).resolve().parents[2]   # .../medibot
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"

DOC_DIRS = {
    "general": DATA_DIR / "general",
    "clinical": DATA_DIR / "clinical",
    "nursing": DATA_DIR / "nursing",
    "billing": DATA_DIR / "billing",
    "equipment": DATA_DIR / "equipment",
}

SQLITE_PATH = DATA_DIR / "mediassist.db"
MEDIASSIST_DB_PATH = "backend/data/db/mediassist.db"
QDRANT_PATH = str(BACKEND_DIR / "qdrant_db")

# =====================================================================
# MODELS
# =====================================================================
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2" # (Legacy, replaced by Jev)

# Note: LiteLLM requires the 'groq/' prefix for Groq models
ROUTER_MODEL = "groq/llama-3.1-8b-instant"
SYNTHESIS_MODEL = "deepseek/deepseek-chat"
SQL_MODEL = "groq/llama-3.3-70b-versatile"

# =====================================================================
# QDRANT SETTINGS
# =====================================================================
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # None for local
QDRANT_COLLECTION = "medibot_hybrid"

# =====================================================================
# AUTHENTICATION
# =====================================================================
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGO = "HS256"