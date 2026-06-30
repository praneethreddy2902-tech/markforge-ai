"""
src/pdf_pipeline.py
PDF document pipeline for MarkForge AI.

Replaces URL scraping (steps 1-4) with PDF text extraction.
Steps 5-16 (clean → chunk → embed → store → retrieve → generate → poster)
are identical to run_pipeline so the output format is the same.

Usage:
    from src.pdf_pipeline import run_pdf_pipeline
    res = run_pdf_pipeline(pdf_bytes, filename="nike_brand_guide.pdf")
"""

import io
import re
import time
import logging

import config

from src.data_processing.cleaner      import clean_text
from src.data_processing.preprocessor import preprocess
from src.chunking.chunker             import chunk_text, enrich_chunks
from src.embeddings.embedder          import embed_chunks
from src.database                     import store_embeddings
from src.retrieval.retriever          import retrieve_relevant_chunks, format_context
from src.llm_service.claude_api       import get_claude_response
from src.llm_service.prompt_templates import get_marketing_prompt, build_poster_html
from src.output_formatter.formatter   import parse_marketing_response

logger = logging.getLogger(__name__)


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract full text from PDF bytes using pypdf.
    Concatenates text from all pages with double newlines between them.
    Raises RuntimeError if pypdf is not installed or extraction fails.
    """
    try:
        import pypdf
    except ImportError:
        raise RuntimeError(
            "pypdf is required for PDF support. "
            "Install it with: pip install pypdf"
        )

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {e}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _brand_name_from_filename(filename: str) -> str:
    """
    Derive a display name from the PDF filename.
    "nike_brand_guidelines_2024.pdf" → "Nike"
    "Apple Brand Standards.pdf"      → "Apple Brand Standards"
    """
    name = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE)
    name = re.sub(r"[_\-]+", " ", name).strip()
    words = name.split()
    if not words:
        return "Brand"
    # If user already used title-case, preserve it
    if any(w[0].isupper() for w in words if w):
        return " ".join(words[:4])           # cap at 4 words for display
    return " ".join(w.capitalize() for w in words[:4])


def _pdf_error(msg: str, start_time: float, logs: list) -> dict:
    logger.error(msg)
    logs.append(f"ERROR: {msg}")
    return {
        "success":           False,
        "raw_response":      "",
        "parsed_output":     {},
        "brand_assets":      {},
        "latency":           round(time.time() - start_time, 2),
        "chunks_used":       0,
        "avg_similarity":    0.0,
        "retrieved_context": "",
        "from_cache":        False,
        "logs":              logs,
        "error":             msg,
    }


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pdf_pipeline(pdf_bytes: bytes, filename: str) -> dict:
    """
    Run the MarkForge AI RAG pipeline on an uploaded PDF document.

    Steps 1-4 (URL validation / scraping / brand extraction) are replaced
    by PDF text extraction.  Steps 5-16 (RAG + generation + poster) are
    identical to run_pipeline so the result dict is the same shape.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.
        filename:  Original filename — used for brand name inference
                   and as the ChromaDB source key.

    Returns:
        Unified result dict with keys:
            success, raw_response, parsed_output, brand_assets,
            latency, chunks_used, avg_similarity, retrieved_context,
            from_cache, source_key, logs, error
    """
    start_time = time.time()
    logs: list = []

    def log(msg: str):
        logger.info(msg)
        logs.append(msg)

    # Synthetic source key — used for ChromaDB collection scoping.
    # Must be stable across reruns of the same file.
    source_key = f"pdf::{filename}"
    brand_name = _brand_name_from_filename(filename)

    # Default brand assets — no HTML scraping, no brand registry
    brand_assets: dict = {
        "brand_name":       brand_name,
        "description":      f"Brand document: {filename}",
        "tone":             "professional",
        "logo_url":         "",
        "primary_color":    "#1a1a2e",
        "secondary_color":  "#e63946",
        "brand_colors":     [],
        "product_images":   [],
        "unsplash_credits": [],
    }

    log(f"PDF pipeline started — file: {filename} | brand: {brand_name}")

    # ── Step 1: Extract text from PDF ────────────────────────────────────────
    log(f"Extracting text from PDF ({len(pdf_bytes) // 1024} KB)...")
    try:
        raw_text = extract_pdf_text(pdf_bytes)
        log(f"Extracted {len(raw_text):,} chars from {len(raw_text.split())} words")
    except RuntimeError as e:
        return _pdf_error(str(e), start_time, logs)

    word_count = len(raw_text.split())
    if word_count < 80:
        return _pdf_error(
            f"PDF has too little readable text ({word_count} words). "
            "Is this a scanned / image-only PDF?  "
            "Try a text-based PDF instead.",
            start_time, logs,
        )

    # ── Step 2: Clean text ────────────────────────────────────────────────────
    log("Cleaning text...")
    try:
        cleaned_text = clean_text(raw_text)
    except Exception as e:
        return _pdf_error(f"Text cleaning failed: {e}", start_time, logs)

    # ── Step 3: Preprocess (save to disk) ────────────────────────────────────
    log("Preprocessing...")
    try:
        preprocess(cleaned_text, source_key)
    except Exception as e:
        log(f"Preprocessing warning: {e} — continuing")

    # ── Step 4: Chunk text ────────────────────────────────────────────────────
    log("Chunking text...")
    try:
        chunks = chunk_text(cleaned_text)
        log(f"Created {len(chunks)} chunks")
    except Exception as e:
        return _pdf_error(f"Chunking failed: {e}", start_time, logs)

    # ── Step 5: Enrich chunks ─────────────────────────────────────────────────
    try:
        enriched_chunks = enrich_chunks(
            chunks=chunks,
            brand_name=brand_name,
            tone="professional",
            description=f"PDF document: {filename}",
        )
    except Exception as e:
        log(f"Chunk enrichment warning: {e} — using raw chunks")
        enriched_chunks = chunks

    # ── Step 6: Embed chunks ──────────────────────────────────────────────────
    log("Generating embeddings (all-MiniLM-L6-v2)...")
    try:
        embeddings = embed_chunks(enriched_chunks)
        log(f"Embedded {len(embeddings)} chunks (384-dim)")
    except Exception as e:
        return _pdf_error(f"Embedding failed: {e}", start_time, logs)

    # ── Step 7: Store in ChromaDB ─────────────────────────────────────────────
    log("Storing embeddings in ChromaDB...")
    try:
        store_embeddings(
            chunks=enriched_chunks,
            embeddings=embeddings,
            source_url=source_key,
        )
    except Exception as e:
        return _pdf_error(f"Vector store failed: {e}", start_time, logs)

    # ── Step 8: Retrieve relevant chunks ──────────────────────────────────────
    log("Retrieving relevant chunks...")
    retrieval_query = (
        f"{brand_name} brand values products marketing campaigns "
        "unique selling points features benefits identity positioning"
    )
    try:
        chunk_results = retrieve_relevant_chunks(
            query=retrieval_query,
            top_k=config.TOP_K_RESULTS,
            url=source_key,
        )
        chunks_used    = len(chunk_results)
        avg_similarity = (
            round(sum(c["score"] for c in chunk_results) / chunks_used, 4)
            if chunk_results else 0.0
        )
        log(f"Retrieved {chunks_used} chunks | avg similarity: {avg_similarity}")
    except Exception as e:
        return _pdf_error(f"Retrieval failed: {e}", start_time, logs)

    # ── Step 9: Format context ────────────────────────────────────────────────
    retrieved_context = format_context(chunk_results)

    # ── Step 10: Build marketing prompt ──────────────────────────────────────
    log("Building marketing prompt...")
    prompt_text = get_marketing_prompt(
        context=retrieved_context,
        source_url=source_key,
        brand_name=brand_name,
        tone="professional",
        description=f"Brand document uploaded as PDF: {filename}",
    )

    # ── Step 11: Call Claude API ──────────────────────────────────────────────
    log("Calling Claude for generation...")
    try:
        raw_response = get_claude_response(
            prompt_text=prompt_text,
            system_prompt="You are an expert marketing strategist. Follow the output format exactly.",
        )
        log(f"Claude response received — {len(raw_response)} chars")
    except Exception as e:
        return _pdf_error(f"LLM call failed: {e}", start_time, logs)

    # ── Step 12: Parse response ───────────────────────────────────────────────
    log("Parsing LLM response...")
    try:
        parsed_output = parse_marketing_response(raw_response)
    except Exception as e:
        log(f"Parse warning: {e} — using empty output")
        parsed_output = {}

    parsed_output["raw_response"] = raw_response

    # Let Claude's inferred brand name override the filename-derived one
    if parsed_output.get("brand_name"):
        brand_assets["brand_name"] = parsed_output["brand_name"]

    taglines  = parsed_output.get("taglines", [])
    para      = parsed_output.get("marketing_paragraph", "")
    features  = parsed_output.get("key_features", [])
    headlines = parsed_output.get("headlines", [])
    cta_line  = parsed_output.get("cta_line", "")

    log(
        f"Parsing complete — brand: {parsed_output.get('brand_name')}, "
        f"personality: {parsed_output.get('brand_personality')}, "
        f"headlines: {len(headlines)}, taglines: {len(taglines)}"
    )

    # ── Step 13: Build poster ─────────────────────────────────────────────────
    log("Building poster HTML...")
    parsed_output["poster_html"] = build_poster_html(
        brand_name=brand_assets["brand_name"],
        taglines=taglines,
        marketing_paragraph=para,
        key_features=features[:3],
        primary_color=brand_assets["primary_color"],
        secondary_color=brand_assets["secondary_color"],
        logo_url="",
        product_images=[],          # no images for PDF mode — uses abstract visual
        headlines=headlines,
        cta_line=cta_line,
        tone=brand_assets.get("tone", "professional"),
        industry=parsed_output.get("industry", ""),
        logo_name=parsed_output.get("logo_name", ""),
        product_category=parsed_output.get("product_category", ""),
    )

    return {
        "success":           True,
        "raw_response":      raw_response,
        "parsed_output":     parsed_output,
        "brand_assets":      brand_assets,
        "latency":           round(time.time() - start_time, 2),
        "chunks_used":       chunks_used,
        "avg_similarity":    avg_similarity,
        "retrieved_context": retrieved_context,
        "from_cache":        False,
        "fallback_used":     False,
        "source_key":        source_key,
        "logs":              logs,
        "error":             None,
    }
