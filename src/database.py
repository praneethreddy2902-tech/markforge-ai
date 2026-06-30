# src/database.py
"""
Vector Database Module (ChromaDB)
-----------------------------------
FIX 3 — URL-Scoped Collections:
  Each URL gets its own collection named "markforge_{url_hash}".
  This prevents retrieval cross-contamination between different URLs.
  Example:
    Nike Wikipedia  → collection "markforge_a1b2c3d4e5"
    Apple Wikipedia → collection "markforge_f6g7h8i9j0"
"""

import os
import hashlib
import logging
from typing import List, Dict, Any

import chromadb

import config

logger = logging.getLogger(__name__)

# Module-level client cache
_client = None


def _get_client():
    """Return persistent ChromaDB client (created once)."""
    global _client
    if _client is None:
        os.makedirs(config.VECTORSTORE_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=config.VECTORSTORE_PATH)
        _client.clear_system_cache() 
    return _client


def _collection_name_for_url(url: str) -> str:
    """
    Generate a deterministic collection name for a URL.
    Format: "markforge_{10-char-md5-hash}"
    ChromaDB requires names to be 3-63 chars, alphanumeric + underscore.
    """
    normalised = url.strip().lower().rstrip("/")
    url_hash = hashlib.md5(normalised.encode()).hexdigest()[:10]
    return f"markforge_{url_hash}"


def get_collection(url: str = None):
    """
    Returns the ChromaDB collection for a specific URL.
    If url is None, falls back to the default collection (backward compat).

    Args:
        url: The URL being processed. Each URL gets its own collection.

    Returns:
        ChromaDB collection object.
    """
    client = _get_client()

    if url:
        name = _collection_name_for_url(url)
    else:
        name = config.COLLECTION_NAME

    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

    logger.info(
        f"ChromaDB collection '{name}' ready. "
        f"Documents stored: {collection.count()}"
    )

    return collection


def collection_exists_for_url(url: str) -> bool:
    """Check whether a collection already exists for this URL."""
    client = _get_client()
    name = _collection_name_for_url(url)
    try:
        existing = [c.name for c in client.list_collections()]
        return name in existing
    except Exception:
        return False


def store_embeddings(
    chunks:     List[str],
    embeddings: List[List[float]],
    source_url: str,
) -> int:
    """
    Stores chunks and embeddings in the URL-scoped ChromaDB collection.
    Uses upsert — safe to re-run on the same URL without duplicates.

    Args:
        chunks:     Text chunks from chunker.py
        embeddings: Vectors from embedder.py (one per chunk)
        source_url: The URL being processed

    Returns:
        Number of chunks stored.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Chunks ({len(chunks)}) and embeddings "
            f"({len(embeddings)}) must have the same length."
        )

    collection = get_collection(source_url)

    # Deterministic IDs based on URL hash + chunk index
    url_hash  = hashlib.md5(source_url.strip().lower().rstrip("/").encode()).hexdigest()[:10]
    ids       = [f"{url_hash}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source_url, "chunk_index": i}
                 for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(
        f"Stored {len(chunks)} chunks for {source_url}. "
        f"Collection: {collection.name} | Total: {collection.count()}"
    )

    return len(chunks)


def get_collection_stats(url: str = None) -> Dict[str, Any]:
    """
    Returns basic stats about the collection for a URL.

    Args:
        url: If provided, returns stats for that URL's collection.
             If None, returns stats for the default collection.
    """
    collection = get_collection(url)
    return {
        "collection_name":  collection.name,
        "total_documents":  collection.count(),
        "vectorstore_path": config.VECTORSTORE_PATH,
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    test_url = "https://en.wikipedia.org/wiki/Nike,_Inc."

    print(f"Collection name for Nike: {_collection_name_for_url(test_url)}")
    print(f"Collection exists: {collection_exists_for_url(test_url)}")

    stats = get_collection_stats(test_url)
    print(f"Stats: {stats}")