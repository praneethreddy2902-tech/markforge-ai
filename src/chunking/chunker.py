# src/chunking/chunker.py
"""
Text Chunking Module
---------------------
Splits cleaned text into overlapping chunks using LangChain.
This is Step 3 of the pipeline: Chunking.

Document reference:
  §1  : RAG pipeline — chunks are the unit of embedding and retrieval
  Synopsis: LangChain RecursiveCharacterTextSplitter with overlap
"""

import os
import logging
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

import config

logger = logging.getLogger(__name__)


def chunk_text(cleaned_text: str) -> List[str]:
    """
    Splits cleaned text into overlapping chunks using LangChain's
    RecursiveCharacterTextSplitter.

    Why RecursiveCharacterTextSplitter?
    - Tries to split on paragraphs first, then sentences, then words
    - Only splits mid-word as a last resort
    - Preserves semantic continuity better than a fixed character split

    Why overlap?
    - A sentence can span the boundary between two chunks
    - Overlap ensures that boundary content appears in both chunks
    - This prevents relevant context from being lost during retrieval

    Args:
        cleaned_text: Output from cleaner.clean_text()

    Returns:
        List of text chunk strings, each ~CHUNK_SIZE characters.

    Raises:
        ValueError: If cleaned_text is empty.
    """
    if not cleaned_text or not cleaned_text.strip():
        raise ValueError("Cannot chunk empty text.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,         # max chars per chunk (500)
        chunk_overlap=config.CHUNK_OVERLAP,   # overlap between chunks (50)
        length_function=len,                  # measure size by character count
        separators=["\n\n", "\n", ". ", " ", ""]
        # tries these separators in order:
        # 1. paragraph break  (\n\n) — best split point
        # 2. line break       (\n)
        # 3. sentence end     (. )
        # 4. word boundary    ( )
        # 5. character        ("") — last resort only
    )

    chunks = splitter.split_text(cleaned_text)

    logger.info(
        f"Chunking complete — "
        f"{len(cleaned_text)} chars → {len(chunks)} chunks "
        f"(size: {config.CHUNK_SIZE}, overlap: {config.CHUNK_OVERLAP})"
    )

    return chunks

def enrich_chunks(
    chunks: list,
    brand_name: str,
    tone: str,
    description: str = ""
) -> list:
    """
    Prepends brand context to each chunk before embedding.

    Why: Embeddings capture meaning. A chunk about "product quality"
    without brand context is generic. With brand context prepended,
    the embedding knows it's about a specific brand's product quality.
    This improves retrieval relevance for marketing queries.

    Args:
        chunks:      Raw text chunks from chunk_text()
        brand_name:  Extracted brand name
        tone:        Detected brand tone
        description: Meta description (optional)

    Returns:
        List of enriched chunk strings.
    """
    prefix = f"Brand: {brand_name} | Tone: {tone}"
    if description:
        # Add first 60 chars of description as context
        short_desc = description[:60].strip()
        prefix += f" | About: {short_desc}"
    prefix += " | "

    enriched = [prefix + chunk for chunk in chunks]

    logger.info(
        f"Enriched {len(enriched)} chunks with brand context. "
        f"Prefix: '{prefix[:60]}...'"
    )
    return enriched

def log_chunk_stats(chunks: List[str]) -> None:
    """
    Logs statistics about the chunks produced.
    Useful for verifying chunk quality before embedding.

    Args:
        chunks: List of chunk strings from chunk_text()
    """
    if not chunks:
        logger.warning("No chunks to report stats for.")
        return

    sizes      = [len(c) for c in chunks]
    avg_size   = sum(sizes) // len(sizes)
    min_size   = min(sizes)
    max_size   = max(sizes)

    logger.info(f"Chunk stats — count: {len(chunks)}, "
                f"avg: {avg_size} chars, "
                f"min: {min_size} chars, "
                f"max: {max_size} chars")


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from src.scraping.scraper import scrape_url
    from src.data_processing.cleaner import clean_text

    test_url = "https://en.wikipedia.org/wiki/Digital_marketing"

    print("Step 1 — Scraping...")
    raw  = scrape_url(test_url, save_raw=False)

    print("Step 2 — Cleaning...")
    cleaned = clean_text(raw)

    print("Step 3 — Chunking...")
    chunks = chunk_text(cleaned)
    log_chunk_stats(chunks)

    print("\n" + "="*50)
    print("CHUNKING TEST RESULT")
    print("="*50)
    print(f"Total chunks     : {len(chunks)}")
    print(f"Chunk size config: {config.CHUNK_SIZE} chars")
    print(f"Overlap config   : {config.CHUNK_OVERLAP} chars")

    print(f"\n--- Chunk 1 ---\n{chunks[0]}")
    print(f"\n--- Chunk 2 ---\n{chunks[1]}")
    print(f"\n--- Last Chunk ---\n{chunks[-1]}")