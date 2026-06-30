# src/embeddings/embedder.py
"""
Embeddings Module
------------------
Converts text chunks into semantic vectors using sentence-transformers.
This is Step 4 of the pipeline: Embedding.

Document reference:
  §1  : RAG pipeline — convert chunks into embeddings
  Synopsis: sentence-transformers, all-MiniLM-L6-v2, 384-dimensional vectors
"""

import logging
from typing import List

from sentence_transformers import SentenceTransformer

import config

logger = logging.getLogger(__name__)

# ── Load model once at module level — expensive to reload every call ──────────
# Downloads ~90MB on first run, then cached locally
_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the embedding model, loading it only once.
    Uses a module-level cache so it's not reloaded on every call.

    Returns:
        Loaded SentenceTransformer model.
    """
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Embedding model loaded and cached.")
    return _model


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """
    Converts a list of text chunks into a list of embedding vectors.

    Each chunk → one vector of 384 floats.
    Semantically similar chunks produce vectors that are close
    together in 384-dimensional space.

    Args:
        chunks: List of text strings from chunker.py

    Returns:
        List of embedding vectors — one per chunk.
        Each vector is a list of 384 floats.

    Raises:
        ValueError: If chunks list is empty.
    """
    if not chunks:
        raise ValueError("Cannot embed empty chunk list.")

    model = get_embedding_model()

    logger.info(f"Embedding {len(chunks)} chunks...")

    # encode() returns a numpy array of shape (n_chunks, 384)
    # .tolist() converts it to a plain Python list of lists
    embeddings = model.encode(
        chunks,
        show_progress_bar=True,
        batch_size=32          # process 32 chunks at a time for efficiency
    ).tolist()

    logger.info(
        f"Embedding complete — "
        f"{len(embeddings)} vectors, "
        f"{len(embeddings[0])} dimensions each"
    )

    return embeddings