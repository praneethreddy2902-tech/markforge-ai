# src/output_formatter/formatter.py
"""
Output Formatter Module
------------------------
Parses raw LLM response into clean Python objects.
This is the final processing step before Streamlit display.
"""

import re
import logging

logger = logging.getLogger(__name__)


def extract_field(response: str, field_name: str) -> str:
    """
    Extracts a single field value and strips markdown artifacts.
    Handles multi-word field names with underscores.
    """
    pattern = rf"^{re.escape(field_name)}:\s*(.+?)$"
    match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
    if match:
        value = match.group(1).strip()
        # Remove markdown artifacts: **, *, ##, __
        value = re.sub(r"\*+|#{1,6}\s*|__", "", value).strip()
        return value
    return ""


def parse_marketing_response(raw_response: str) -> dict:
    """
    Master parsing function — converts raw LLM response into a structured dict.

    Returns:
        {
            # Brand intelligence
            brand_personality, target_audience, emotional_appeal,
            visual_direction, marketing_tone, color_style,

            # Core fields
            brand_name, industry,
            headlines,       ← list of 3 billboard headlines
            taglines,        ← list of 3 taglines
            social_post,
            cta_line,
            marketing_paragraph,
            key_features,
            poster_prompt,
            raw_response
        }
    """
    logger.info("Parsing LLM response...")

    # ── Brand intelligence ────────────────────────────────────────────────────
    brand_personality = extract_field(raw_response, "BRAND_PERSONALITY")
    target_audience   = extract_field(raw_response, "TARGET_AUDIENCE")
    emotional_appeal  = extract_field(raw_response, "EMOTIONAL_APPEAL")
    visual_direction  = extract_field(raw_response, "VISUAL_DIRECTION")
    marketing_tone    = extract_field(raw_response, "MARKETING_TONE")
    color_style       = extract_field(raw_response, "COLOR_STYLE")

    # ── Core content ──────────────────────────────────────────────────────────
    brand_name  = extract_field(raw_response, "BRAND_NAME")
    industry    = extract_field(raw_response, "INDUSTRY")

    headline_1  = extract_field(raw_response, "HEADLINE_1")
    headline_2  = extract_field(raw_response, "HEADLINE_2")
    headline_3  = extract_field(raw_response, "HEADLINE_3")

    tagline_1   = extract_field(raw_response, "TAGLINE_1")
    tagline_2   = extract_field(raw_response, "TAGLINE_2")
    tagline_3   = extract_field(raw_response, "TAGLINE_3")

    social_post = extract_field(raw_response, "SOCIAL_POST")
    cta_line    = extract_field(raw_response, "CTA_LINE")
    marketing_paragraph = extract_field(raw_response, "MARKETING_PARAGRAPH")

    feature_1   = extract_field(raw_response, "KEY_FEATURE_1")
    feature_2   = extract_field(raw_response, "KEY_FEATURE_2")
    feature_3   = extract_field(raw_response, "KEY_FEATURE_3")

    logo_name         = extract_field(raw_response, "LOGO_NAME")
    product_category  = extract_field(raw_response, "PRODUCT_CATEGORY")
    poster_prompt     = extract_field(raw_response, "POSTER_PROMPT")

    result = {
        # Brand intelligence
        "brand_personality": brand_personality,
        "target_audience":   target_audience,
        "emotional_appeal":  emotional_appeal,
        "visual_direction":  visual_direction,
        "marketing_tone":    marketing_tone,
        "color_style":       color_style,

        # Core content
        "brand_name":          brand_name or "Unknown Brand",
        "industry":            industry   or "Unknown Industry",
        "headlines":           [h for h in [headline_1, headline_2, headline_3] if h],
        "taglines":            [t for t in [tagline_1, tagline_2, tagline_3] if t],
        "social_post":         social_post or "",
        "cta_line":            cta_line or "",
        "marketing_paragraph": marketing_paragraph or "",
        "key_features":        [f for f in [feature_1, feature_2, feature_3] if f],
        "logo_name":           logo_name or "",
        "product_category":    product_category or "",
        "poster_prompt":       poster_prompt or "",
        "raw_response":        raw_response,
    }

    logger.info(
        f"Parsing complete — brand: {result['brand_name']}, "
        f"personality: {result['brand_personality']}, "
        f"headlines: {len(result['headlines'])}, "
        f"taglines: {len(result['taglines'])}"
    )

    return result
