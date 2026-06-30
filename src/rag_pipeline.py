"""
src/rag_pipeline.py
Master orchestrator for the MarkForge AI RAG pipeline.

16-step sequential pipeline:
  0.  Cache check — return instantly if hit + vectors exist
  1.  validate_url()
  2.  fetch_page()
  3.  extract_brand_assets()           [uses same HTML]
  4.  extract_text() via BeautifulSoup [uses same HTML]
  5.  check_content_length()
  6.  clean_text()
  7.  preprocess()
  8.  chunk_text()
  9.  enrich_chunks()
  10. embed_chunks()
  11. store_embeddings()
  12. retrieve_relevant_chunks()  → avg_similarity
  13. format_context()            → context string for prompt
  14. get_marketing_prompt()
  15. get_claude_response()
  16. parse_marketing_response() → build_poster_html() → cache.save() → return
"""

import time
import logging

import config

from src.cache                        import save as cache_save, load as cache_load
from src.scraping.utils               import validate_url, check_content_length
from src.scraping.scraper             import fetch_page, extract_text
from src.scraping.brand_extractor     import extract_brand_assets, fetch_image_as_base64
from src.scraping.unsplash_fetcher    import fetch_brand_images as unsplash_fetch
from src.scraping.brand_registry      import get_wikipedia_fallback, get_visual_hints, get_clean_name
from src.data_processing.cleaner      import clean_text
from src.data_processing.preprocessor import preprocess
from src.chunking.chunker             import chunk_text, enrich_chunks
from src.embeddings.embedder          import embed_chunks
from src.database                     import store_embeddings, collection_exists_for_url
from src.retrieval.retriever          import retrieve_relevant_chunks, format_context
from src.llm_service.claude_api       import get_claude_response
from src.llm_service.prompt_templates import get_marketing_prompt, build_poster_html
from src.output_formatter.formatter   import parse_marketing_response

logger = logging.getLogger(__name__)


def run_pipeline(
    url: str,
    query: str = "",
    force_refresh: bool = False,
) -> dict:
    """
    Run the full MarkForge AI RAG pipeline for a given URL.

    Args:
        url:           Target website URL to scrape and generate content for.
        query:         Optional custom retrieval query.
        force_refresh: If True, bypass cache and re-run the full pipeline.

    Returns:
        Unified result dict with keys:
            success, raw_response, parsed_output, brand_assets,
            latency, chunks_used, avg_similarity, retrieved_context,
            from_cache, logs, error
    """
    start_time = time.time()
    logs = []

    def log(msg: str):
        logger.info(msg)
        logs.append(msg)

   
    cached = cache_load(url, force_refresh=force_refresh)
    if cached:
        log("✓ Cache hit — loading from disk")

        brand_assets  = cached["brand_assets"]
        parsed_output = cached["parsed_output"]

        
        logo_url = brand_assets.get("logo_url", "")
        if logo_url and not logo_url.startswith("data:"):
            logo_b64 = fetch_image_as_base64(logo_url)
            if logo_b64:
                brand_assets["logo_url"] = logo_b64

        product_images = brand_assets.get("product_images", [])
        product_b64 = []
        for img_url in product_images[:3]:
            if img_url.startswith("data:"):
                product_b64.append(img_url)
            else:
                b64 = fetch_image_as_base64(img_url)
                if b64:
                    product_b64.append(b64)
        brand_assets["product_images"] = product_b64

        taglines  = parsed_output.get("taglines", [])
        para      = parsed_output.get("marketing_paragraph", "")
        features  = parsed_output.get("key_features", [])
        headlines = parsed_output.get("headlines", [])
        cta_line  = parsed_output.get("cta_line", "")

        parsed_output["poster_html"] = build_poster_html(
            brand_name=brand_assets.get("brand_name", "Brand"),
            taglines=taglines,
            marketing_paragraph=para,
            key_features=features[:3],
            primary_color=brand_assets.get("primary_color", "#1a1a2e"),
            secondary_color=brand_assets.get("secondary_color", "#e63946"),
            logo_url=brand_assets.get("logo_url", ""),
            product_images=brand_assets.get("product_images", []),
            headlines=headlines,
            cta_line=cta_line,
            tone=brand_assets.get("tone", ""),
            industry=parsed_output.get("industry", ""),
            logo_name=parsed_output.get("logo_name", ""),
            product_category=parsed_output.get("product_category", ""),
        )

        return {
            "success":           True,
            "raw_response":      parsed_output.get("raw_response", ""),
            "parsed_output":     parsed_output,
            "brand_assets":      brand_assets,
            "latency":           round(time.time() - start_time, 2),
            "chunks_used":       5,
            "avg_similarity":    0.0,
            "retrieved_context": "",
            "from_cache":        True,
            "logs":              logs,
            "error":             None,
        }

    
    log(f"Validating URL: {url}")
    is_valid, validation_msg = validate_url(url)
    if not is_valid:
        return _error_result(validation_msg, start_time, logs)

    
    official_marketing_text = None
    is_wikipedia = "wikipedia.org" in url.lower()

    if not is_wikipedia:
        log("Attempting official site content extraction...")
        try:
            from src.scraping.official_scraper import scrape_official_brand_site
            official_result = scrape_official_brand_site(url, timeout=12)
            if official_result["success"] and official_result["word_count"] >= 150:
                official_marketing_text = official_result["marketing_text"]
                log(
                    f"Official site extraction SUCCESS — "
                    f"{official_result['word_count']} words, "
                    f"{len(official_result.get('hero_texts', []))} hero sections, "
                    f"{len(official_result.get('cta_texts', []))} CTAs"
                )
            else:
                log(
                    f"Official site extraction skipped "
                    f"({official_result.get('error', 'insufficient content')}) "
                    f"— falling back to standard scraper"
                )
        except ImportError:
            log("official_scraper not found — using standard scraper only")
        except Exception as e:
            log(f"Official site extraction failed ({e}) — falling back")

   
    log("Fetching page HTML...")
    scrape_url = url          
    fallback_used = False
    try:
        raw_html = fetch_page(url)
    except Exception as e:
        wiki_url = get_wikipedia_fallback(url)
        if wiki_url:
            log(f"Direct scrape blocked — trying Wikipedia fallback: {wiki_url}")
            try:
                raw_html   = fetch_page(wiki_url)
                scrape_url = wiki_url
                fallback_used = True
                log("Wikipedia fallback succeeded")
            except Exception as e2:
                return _error_result(
                    f"Scraping failed: {e} | Wikipedia fallback also failed: {e2}",
                    start_time, logs
                )
        else:
            return _error_result(f"Scraping failed: {e}", start_time, logs)

    
    log("Extracting brand assets...")
    try:
        brand_assets = extract_brand_assets(raw_html, scrape_url)
        log(
            f"Brand: {brand_assets.get('brand_name')} | "
            f"Tone: {brand_assets.get('tone')} | "
            f"Logo: {bool(brand_assets.get('logo_url'))}"
        )
    except Exception as e:
        log(f"Brand extraction warning: {e} — using defaults")
        brand_assets = {
            "brand_name":      _domain_fallback(url),
            "description":     "",
            "tone":            "professional",
            "logo_url":        "",
            "primary_color":   "#1a1a2e",
            "secondary_color": "#e63946",
            "brand_colors":    [],
            "product_images":  [],
        }

    
    visual_hints = get_visual_hints(url)
    if visual_hints:
        if visual_hints.get("primary_color"):
            brand_assets["primary_color"]   = visual_hints["primary_color"]
        if visual_hints.get("secondary_color"):
            brand_assets["secondary_color"] = visual_hints["secondary_color"]
        if visual_hints.get("tone"):
            brand_assets["tone"]            = visual_hints["tone"]
        log(f"Registry hints applied — accent: {visual_hints.get('secondary_color')}, tone: {visual_hints.get('tone')}")

    clean_name = get_clean_name(url)
    if clean_name:
        brand_assets["brand_name"] = clean_name
        log(f"Brand name set from registry: {clean_name}")

    if fallback_used:
        brand_assets["_fallback_note"] = f"Content sourced from Wikipedia (direct site blocked)"
        log("Fallback note stored in brand_assets")

   
    if config.UNSPLASH_ACCESS_KEY:
        log(f"Fetching Unsplash images for '{brand_assets.get('brand_name', '')}'...")
        u_urls, u_credits = unsplash_fetch(
            brand_name=brand_assets.get("brand_name", ""),
            description=brand_assets.get("description", ""),
            access_key=config.UNSPLASH_ACCESS_KEY,
            count=3,
            custom_query=visual_hints.get("unsplash_query", ""),
        )
        if u_urls:
            brand_assets["product_images"]    = u_urls
            brand_assets["unsplash_credits"]  = u_credits
            log(f"Unsplash: {len(u_urls)} images ready")
        else:
            log("Unsplash returned no results — keeping HTML-scraped images")
            brand_assets.setdefault("unsplash_credits", [])
    else:
        brand_assets.setdefault("unsplash_credits", [])

   
    log("Resolving images to base64...")
    logo_b64 = fetch_image_as_base64(brand_assets.get("logo_url", ""))
    if logo_b64:
        brand_assets["logo_url"] = logo_b64
        log("Logo embedded as base64")
    else:
        log("Logo not available — will show brand name text")

    product_b64 = []
    for img_url in brand_assets.get("product_images", [])[:3]:
        b64 = fetch_image_as_base64(img_url)
        if b64:
            product_b64.append(b64)
    if product_b64:
        log(f"{len(product_b64)} product image(s) embedded as base64")
        brand_assets["product_images"] = product_b64
    else:
        brand_assets["product_images"] = []
        log("No product images — poster grid will use placeholder colors")

    
    log("Extracting text content...")
    try:
        raw_text = extract_text(raw_html)
        log(f"Extracted {len(raw_text)} chars of text")
    except Exception as e:
        return _error_result(f"Text extraction failed: {e}", start_time, logs)

    
    if official_marketing_text:
        raw_text = official_marketing_text + "\n\n" + raw_text
        log(f"Official marketing content prepended — total {len(raw_text)} chars")

   
    _word_count = len(raw_text.split())
    if _word_count < 80 and not fallback_used:
        wiki_url = get_wikipedia_fallback(url)
        if wiki_url:
            log(
                f"Scraped content too sparse ({_word_count} words) "
                f"— retrying via Wikipedia: {wiki_url}"
            )
            try:
                wiki_html = fetch_page(wiki_url)
                wiki_text = extract_text(wiki_html)
                if len(wiki_text.split()) > _word_count:
                    raw_html      = wiki_html
                    raw_text      = wiki_text
                    scrape_url    = wiki_url
                    fallback_used = True
                    brand_assets["_fallback_note"] = (
                        "Content sourced from Wikipedia (brand site returned sparse content)"
                    )
                    log(f"Wikipedia fallback succeeded — {len(wiki_text.split())} words")
                else:
                    log("Wikipedia content also sparse — continuing with original")
            except Exception as e:
                log(f"Wikipedia sparse-content fallback failed: {e}")

    
    is_long_enough, length_msg = check_content_length(raw_text)
    if not is_long_enough:
        return _error_result(length_msg, start_time, logs)

   
    log("Cleaning text...")
    try:
        cleaned_text = clean_text(raw_text)
    except Exception as e:
        return _error_result(f"Text cleaning failed: {e}", start_time, logs)

    
    log("Preprocessing text...")
    try:
        preprocess(cleaned_text, url)
    except Exception as e:
        log(f"Preprocessing warning: {e} — continuing")

    
    log("Chunking text...")
    try:
        chunks = chunk_text(cleaned_text)
        log(f"Created {len(chunks)} chunks")
    except Exception as e:
        return _error_result(f"Chunking failed: {e}", start_time, logs)

    
    log("Enriching chunks with brand context...")
    try:
        enriched_chunks = enrich_chunks(
            chunks=chunks,
            brand_name=brand_assets.get("brand_name", ""),
            tone=brand_assets.get("tone", ""),
            description=brand_assets.get("description", ""),
        )
    except Exception as e:
        log(f"Chunk enrichment warning: {e} — using raw chunks")
        enriched_chunks = chunks

    
    log("Generating embeddings...")
    try:
        embeddings = embed_chunks(enriched_chunks)
        log(f"Embedded {len(embeddings)} chunks (384-dim vectors)")
    except Exception as e:
        return _error_result(f"Embedding failed: {e}", start_time, logs)

   
    log("Storing embeddings in ChromaDB...")
    try:
        store_embeddings(
            chunks=enriched_chunks,
            embeddings=embeddings,
            source_url=url,
        )
    except Exception as e:
        return _error_result(f"Vector store failed: {e}", start_time, logs)

   
    log("Retrieving relevant chunks...")
    retrieval_query = query or (
        f"{brand_assets.get('brand_name', '')} brand values products "
        f"marketing campaigns {brand_assets.get('tone', '')} unique selling "
        f"points features benefits"
    )
    try:
        chunk_results = retrieve_relevant_chunks(
            query=retrieval_query,
            top_k=config.TOP_K_RESULTS,
            url=url,
        )
        chunks_used    = len(chunk_results)
        avg_similarity = (
            round(sum(c["score"] for c in chunk_results) / chunks_used, 4)
            if chunk_results else 0.0
        )
        log(f"Retrieved {chunks_used} chunks | avg similarity: {avg_similarity}")
        for i, c in enumerate(chunk_results, 1):
            log(
                f"  Chunk {i}: similarity={c['score']:.4f}, "
                f"source={c.get('source', url)[:60]}, "
                f"preview={c.get('text', '')[:80]}"
            )
    except Exception as e:
        return _error_result(f"Retrieval failed: {e}", start_time, logs)

    
    retrieved_context = format_context(chunk_results)

   
    log("Building marketing prompt...")
    prompt_text = get_marketing_prompt(
        context=retrieved_context,
        source_url=url,
        brand_name=brand_assets.get("brand_name", ""),
        tone=brand_assets.get("tone", "professional"),
        description=brand_assets.get("description", ""),
    )

    
    log("Calling Claude for generation...")
    system_prompt = (
        "You are an expert marketing strategist. Follow the output format exactly."
    )
    try:
        raw_response = get_claude_response(
            prompt_text=prompt_text,
            system_prompt=system_prompt,
        )
        log(f"Claude response received — {len(raw_response)} chars")
    except Exception as e:
        return _error_result(f"LLM call failed: {e}", start_time, logs)

    
    log("Parsing LLM response...")
    try:
        parsed_output = parse_marketing_response(raw_response)
    except Exception as e:
        log(f"Parse warning: {e} — using empty output")
        parsed_output = {}

    parsed_output["raw_response"] = raw_response

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

    log("Building poster HTML...")
    parsed_output["poster_html"] = build_poster_html(
        brand_name=brand_assets.get("brand_name", parsed_output.get("brand_name", "Brand")),
        taglines=taglines,
        marketing_paragraph=para,
        key_features=features[:3],
        primary_color=brand_assets.get("primary_color", "#1a1a2e"),
        secondary_color=brand_assets.get("secondary_color", "#e63946"),
        logo_url=brand_assets.get("logo_url", ""),
        product_images=brand_assets.get("product_images", []),
        headlines=headlines,
        cta_line=cta_line,
        tone=brand_assets.get("tone", ""),
        industry=parsed_output.get("industry", ""),
        logo_name=parsed_output.get("logo_name", ""),
        product_category=parsed_output.get("product_category", ""),
    )

    try:
        cache_save(url, brand_assets=brand_assets, parsed_output=parsed_output)
        log("Result cached successfully")
    except Exception as e:
        log(f"Cache save warning: {e}")

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
        "fallback_used":     fallback_used,
        "logs":              logs,
        "error":             None,
    }



def _error_result(msg: str, start_time: float, logs: list) -> dict:
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


def _domain_fallback(url: str) -> str:
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        parts  = domain.replace("www.", "").split(".")
        return parts[0].capitalize() if parts else "Brand"
    except Exception:
        return "Brand"