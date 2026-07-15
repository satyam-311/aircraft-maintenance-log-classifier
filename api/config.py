"""
Central configuration. Every environment-dependent value (paths, secrets, mode flags)
is read here, ONCE, from .env -- nothing else in the codebase should call os.getenv()
directly or hardcode a path/key. This matches the Security & Access doc's requirement:
"All secrets live in a local .env file (gitignored)...never committed, never read
directly with hardcoded strings inside route handlers."
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = Path(os.getenv("MODEL_DIR", "models"))
ATA_MODEL_PATH = BASE_DIR / MODEL_DIR / "ata_classifier"
SEVERITY_MODEL_PATH = BASE_DIR / MODEL_DIR / "severity_classifier"
EMBEDDING_MODEL_PATH = BASE_DIR / MODEL_DIR / "embedding_model"

# If set, models are downloaded from Hugging Face Hub at startup instead of read from
# a local folder -- used in deployment (Render), where MODEL_DIR won't already contain
# the trained weights (they're too large for the git repo, ~600MB total).
# Leave unset for local/sandbox use, where models/ already has the files.
HF_ATA_MODEL_REPO = os.getenv("HF_ATA_MODEL_REPO", "")
HF_SEVERITY_MODEL_REPO = os.getenv("HF_SEVERITY_MODEL_REPO", "")
HF_EMBEDDING_MODEL_REPO = os.getenv("HF_EMBEDDING_MODEL_REPO", "")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/processed/reports.db")
CHROMA_PERSIST_DIR = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "data/processed/chroma_index")

ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV == "production"

# The deployed frontend's URL, needed for CORS in production (dev mode allows all
# origins for convenience; production must be locked down per the Security doc's
# "ENV toggles debug logging and CORS rules").
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# Only needed once the /ask (RAG) endpoint is built (Ticket 11). Empty string, not None,
# so downstream code can do a simple truthiness check without a KeyError.
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Thresholds referenced by the Security & Access doc's error-handling table
LOW_CONFIDENCE_THRESHOLD = 0.4
MAX_NARRATIVE_TOKENS = 256
MIN_NARRATIVE_WORDS = 3
