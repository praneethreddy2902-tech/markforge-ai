# config.py
"""
Central configuration file.
All modules import from here. Never hardcode settings elsewhere.
Document reference: §2 (API key handling), §10 (project structure)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API (§2) ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise EnvironmentError(
        "ANTHROPIC_API_KEY not found. "
        "Create a .env file with: ANTHROPIC_API_KEY=your_key_here"
    )

# Unsplash API — optional. Get a free key at https://unsplash.com/developers
# When set, the pipeline fetches 3 high-quality brand photos for the poster grid.
# When empty, falls back to images scraped from the brand's website.
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_ENABLED = bool(UNSPLASH_ACCESS_KEY)  # auto-disables if key missing
UNSPLASH_PER_PAGE = 3

# ── Model ────────────────────────────────────────────────────────────────────
# Corrected from document (§2) — claude-3-opus-20240229 is deprecated
CLAUDE_MODEL = "claude-sonnet-4-5"
MAX_TOKENS   = 2048

# ── RAG settings (§1 pipeline) ───────────────────────────────────────────────
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
TOP_K_RESULTS   = 5
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "markforge_chunks"

# ── Retry settings (§6 — Error Handling) ────────────────────────────────────
RETRY_MAX_ATTEMPTS  = 5
RETRY_WAIT_MIN_SECS = 4
RETRY_WAIT_MAX_SECS = 10

# ── Paths (§10) ──────────────────────────────────────────────────────────────
RAW_DATA_PATH       = "data/raw"
PROCESSED_DATA_PATH = "data/processed"
VECTORSTORE_PATH    = "data/vectorstore"
CACHE_PATH = "data/cache"   

# ── Local Model Toggle (Ollama) ──────────────────────────────
# Set True to use Ollama locally (free, no API key needed)
# Set False to use Claude API (production, needs API key)
USE_LOCAL_MODEL = False 
LOCAL_MODEL     = "llama3"
LOCAL_BASE_URL  = "http://localhost:11434"