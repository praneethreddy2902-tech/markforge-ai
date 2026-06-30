# src/retrieval/retriever.py
"""
Retrieval Module
-----------------
FIX 3 — URL-scoped retrieval:
  Each URL queries its own ChromaDB collection.
  Prevents Nike chunks appearing in Apple results.

FIX 5 — Retrieval Deduplication:
  After fetching top-K chunks, removes near-duplicates.
  Uses trigram overlap to detect similarity between chunks.
  Keeps only diverse chunks so Claude gets varied context.
"""

import logging
from typing import List

from src.embeddings.embedder import get_embedding_model
from src.database            import get_collection

import config

logger = logging.getLogger(__name__)


# ── Deduplication ─────────────────────────────────────────────────────────────

def _trigrams(text: str) -> set:
    """Convert text to a set of character trigrams."""
    text = text.lower().strip()
    return {text[i:i+3] for i in range(len(text) - 2)}


def _trigram_similarity(text_a: str, text_b: str) -> float:
    """
    Jaccard similarity between trigram sets of two strings.
    Returns 0.0 (completely different) to 1.0 (identical).
    """
    tg_a = _trigrams(text_a)
    tg_b = _trigrams(text_b)
    if not tg_a or not tg_b:
        return 0.0
    intersection = len(tg_a & tg_b)
    union        = len(tg_a | tg_b)
    return intersection / union


def deduplicate_chunks(
    chunks: List[dict],
    similarity_threshold: float = 0.6,
) -> List[dict]:
    """
    Remove near-duplicate chunks from retrieved results.

    How it works:
    - Compare every chunk against already-kept chunks
    - If trigram similarity > threshold (60%), skip it as a duplicate
    - Keep the first occurrence (highest similarity score — already sorted)

    Args:
        chunks:               List of chunk dicts {text, source, score}
        similarity_threshold: 0.6 means 60% trigram overlap = duplicate

    Returns:
        Deduplicated list of chunks.
    """
    if not chunks:
        return chunks

    kept = []
    for candidate in chunks:
        is_duplicate = False
        for kept_chunk in kept:
            sim = _trigram_similarity(
                candidate["text"],
                kept_chunk["text"]
            )
            if sim > similarity_threshold:
                logger.info(
                    f"  Dedup: removed chunk with {sim:.2f} similarity "
                    f"to existing chunk"
                )
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(candidate)

    removed = len(chunks) - len(kept)
    if removed > 0:
        logger.info(f"  Dedup: kept {len(kept)}/{len(chunks)} chunks ({removed} duplicates removed)")

    return kept


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_relevant_chunks(
    query: str,
    top_k: int = config.TOP_K_RESULTS,
    url: str = None,
) -> List[dict]:
    """
    Finds the top-K most relevant chunks for a given query.
    Uses the URL-scoped collection if url is provided.
    Applies deduplication before returning.

    Returns list of dicts: {text, source, score}
    """
    collection = get_collection(url)

    if collection.count() == 0:
        raise ValueError(
            "ChromaDB collection is empty. "
            "Run the pipeline first to store embeddings."
        )

    logger.info(f"Retrieving top {top_k} chunks for query: '{query[:60]}...'")

    # Fetch more than needed so deduplication has candidates to work with
    fetch_k = min(top_k * 2, collection.count())

    # Embed query using same model used for chunks
    model           = get_embedding_model()
    query_embedding = model.encode([query]).tolist()

    # Query ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks    = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Build result list
    retrieved = []
    for chunk, meta, dist in zip(chunks, metadatas, distances):
        score = round(1 - dist, 4)
        retrieved.append({
            "text":   chunk,
            "source": meta.get("source", "unknown"),
            "score":  score,
        })
        logger.info(
            f"  Chunk {len(retrieved)}: similarity={score}, "
            f"source={meta.get('source', 'unknown')[:50]}, "
            f"preview='{chunk[:60]}...'"
        )

    # Deduplicate then take top_k
    deduplicated = deduplicate_chunks(retrieved, similarity_threshold=0.6)
    final        = deduplicated[:top_k]

    logger.info(f"Retrieved {len(final)} relevant chunks after deduplication.")
    return final


# ── Formatting ────────────────────────────────────────────────────────────────

def format_context(chunks: List[dict]) -> str:
    """
    Formats retrieved chunks into numbered context string
    ready to inject into Claude's prompt.
    """
    if not chunks:
        return "No relevant context found."

    formatted = []
    for i, chunk in enumerate(chunks, 1):
        formatted.append(f"[Context {i}]\n{chunk['text']}")

    return "\n\n".join(formatted)


# ── Master Function ───────────────────────────────────────────────────────────

def retrieve_and_format(
    query: str = None,
    top_k: int = config.TOP_K_RESULTS,
    url: str = None,
    brand_name: str = "",
    tone: str = "",
) -> str:
    """
    Master retrieval function — the only function the pipeline calls.

    Args:
        query:      Custom query string. If None, builds brand-specific query.
        top_k:      Number of chunks to retrieve.
        url:        URL to scope the collection. Critical for isolation.
        brand_name: Used to build default query if query is None.
        tone:       Used to build default query if query is None.

    Returns:
        Formatted context string ready for Claude's prompt.
    """
    if not query:
        query = (
            f"{brand_name} brand values products marketing campaigns "
            f"{tone} unique selling points features benefits"
        )

    chunks  = retrieve_relevant_chunks(query, top_k, url=url)
    context = format_context(chunks)
    return context