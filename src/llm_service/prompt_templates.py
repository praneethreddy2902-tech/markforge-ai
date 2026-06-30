"""
src/llm_service/prompt_templates.py
All LangChain PromptTemplates and the programmatic poster builder.
"""

from langchain.prompts import PromptTemplate


# ── Marketing Generation Prompt ───────────────────────────────────────────────

MARKETING_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "source_url", "brand_name", "tone", "description"],
    template="""You are a senior brand strategist and creative director at a world-class advertising agency.
Your task: analyze this brand deeply, then generate psychologically-calibrated marketing content.

STEP 1 — BRAND INTELLIGENCE (ground every field in the retrieved context):
Identify the brand's archetype, target audience, emotional hook, visual language, and voice.

STEP 2 — CONTENT GENERATION (let the analysis drive the copy):
Write content that matches the brand's real advertising style — the way Nike uses raw motivation,
Apple uses restraint, or Zomato uses wit. No generic marketing language.

RULES:
- Every output field must reflect the brand's actual identity, not a template
- Zero filler: no "world-class", "innovative solutions", "cutting-edge"
- No ** markdown, no bullet asterisks, no ## headers in output
- SOCIAL_POST max 200 chars including hashtags
- KEY_FEATURE: 2-4 word noun phrase, max 20 chars (e.g. "Speed Focused", "Zero Lag")
- CTA_LINE: 2-4 action words matching brand voice (e.g. "Shop Now", "Start Free", "Explore Today")
- HEADLINE: max 6 words, billboard-style — punchy, zero fluff
- POSTER_PROMPT: 2-3 sentences describing mood, typography, colors, and composition for AI image gen

BRAND: {brand_name}
DETECTED TONE: {tone}
META DESCRIPTION: {description}
SOURCE: {source_url}

<retrieved_context>
{context}
</retrieved_context>

OUTPUT FORMAT (follow exactly — one value per line, no extra lines between fields):

BRAND_PERSONALITY: [archetype — Hero / Creator / Rebel / Sage / Jester / Caregiver / Explorer / Ruler / Lover / Innocent / Outlaw / Magician]
TARGET_AUDIENCE: [1 sentence — who buys this and why they care]
EMOTIONAL_APPEAL: [primary emotion — empowerment / aspiration / trust / joy / belonging / curiosity / pride / nostalgia / urgency]
VISUAL_DIRECTION: [style — e.g. bold & kinetic, minimal & premium, warm & playful, dark & editorial]
MARKETING_TONE: [voice — e.g. commanding, witty & relatable, inspirational, authoritative, conversational, provocative]
COLOR_STYLE: [palette mood — e.g. high-contrast dark, monochrome with red, earth tones, clean white space, neon & electric]
BRAND_NAME: [brand name]
INDUSTRY: [industry in 2-3 words]
HEADLINE_1: [primary campaign headline — max 6 words, billboard style]
HEADLINE_2: [secondary angle — different emotion, max 6 words]
HEADLINE_3: [benefit-led — concrete outcome, max 6 words]
TAGLINE_1: [punchy brand tagline — max 8 words]
TAGLINE_2: [aspirational tagline — max 10 words]
TAGLINE_3: [benefit-led tagline — max 10 words]
SOCIAL_POST: [post with 2-3 relevant hashtags — max 200 chars]
CTA_LINE: [2-4 word action CTA matching brand voice]
MARKETING_PARAGRAPH: [2-3 bold emotionally resonant sentences — no corporate speak]
KEY_FEATURE_1: [2-4 word noun phrase, max 20 chars]
KEY_FEATURE_2: [2-4 word noun phrase, max 20 chars]
KEY_FEATURE_3: [2-4 word noun phrase, max 20 chars]
LOGO_NAME: [brand wordmark — 1-2 words, clean uppercase, no descriptors. Use the exact brand name or a short stylized form. E.g. "NIKE", "APPLE", "NOVA", "AXIS"]
PRODUCT_CATEGORY: [primary product or service in 2-5 words, no brand name. E.g. "Performance Running Shoes", "Cloud Analytics Platform", "Wireless Audio Headphones"]
POSTER_PROMPT: [visual composition for AI image gen — describe mood, typography feel, color palette, subject]""",
)


# ── Chat Q&A Prompt ───────────────────────────────────────────────────────────

CHAT_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question", "source_url"],
    template="""You are a brand intelligence assistant. Answer questions about a brand using ONLY the provided context.

SOURCE: {source_url}

<context>
{context}
</context>

QUESTION: {question}

RULES:
- Answer ONLY from the context above
- If the answer is not in the context, say exactly: "This information is not available in the scraped content."
- Be concise and direct — no preamble
- Do not speculate or add outside knowledge""",
)


# ── Prompt Formatters ─────────────────────────────────────────────────────────

def get_marketing_prompt(
    context: str,
    source_url: str,
    brand_name: str,
    tone: str,
    description: str,
) -> str:
    return MARKETING_PROMPT_TEMPLATE.format(
        context=context,
        source_url=source_url,
        brand_name=brand_name,
        tone=tone,
        description=description,
    )


def get_chat_prompt(context: str, question: str, source_url: str) -> str:
    return CHAT_PROMPT_TEMPLATE.format(
        context=context,
        question=question,
        source_url=source_url,
    )


# ── Poster Builder ────────────────────────────────────────────────────────────
# Poster is ALWAYS built programmatically — never by LLM.

def build_poster_html(
    brand_name: str,
    taglines: list,
    marketing_paragraph: str,
    key_features: list,
    logo_url: str = "",
    primary_color: str = "#1a1a2e",
    secondary_color: str = "#e63946",
    product_images: list = None,
    headlines: list = None,
    cta_line: str = "",
    tone: str = "",
    industry: str = "",
    logo_name: str = "",
    product_category: str = "",
) -> str:
    """
    Build a cinematic full-bleed advertising poster from brand data.

    Tone-aware design system:
    - minimal      (Apple/Tesla)  — Inter, 68px, light weight accent, no clip-path, rounded tags
    - premium      (Dior)         — Cormorant Garamond serif, 74px, editorial elegance
    - bold         (Nike/Adidas)  — Barlow Condensed 86px, aggressive sports aesthetic
    - friendly     (Spotify)      — Barlow Condensed, warmer palette
    - professional (Samsung)      — Inter, clean enterprise feel

    Args:
        brand_name:          Brand name for logo fallback and display
        taglines:            Ghost-text source and subtitle fallback
        marketing_paragraph: Displayed in Streamlit UI (not in poster)
        key_features:        3 short noun-phrase tags in bottom bar
        logo_url:            HTTP URL or base64 data URI of brand logo
        primary_color:       Background tint hex
        secondary_color:     Accent color hex (headlines, CTA, tags)
        product_images:      Up to 3 image URLs/URIs for the grid
        headlines:           LLM billboard headlines (max 6 words each)
        cta_line:            Brand-voice CTA for the button
        tone:                Brand tone from registry (minimal/premium/bold/friendly/professional)
        industry:            Short industry label from LLM output
    """
    product_images = product_images or []
    headlines      = headlines or []
    display_name   = logo_name or brand_name

    is_minimal      = tone == "minimal"
    is_premium      = tone == "premium"
    is_professional = tone == "professional"
    is_clean        = is_minimal or is_premium or is_professional

    accent      = secondary_color.lstrip("#")
    accent_text = "ffffff" if _is_dark(f"#{accent}") else "000000"
    primary     = primary_color.lstrip("#")
    # White ghost on dark backgrounds — elegant at very low opacity
    ghost_color = "ffffff" if is_clean else _lighten(primary, 1.5)

    # ── Font system ──────────────────────────────────────────────────────────
    if is_minimal or is_professional:
        font_url  = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap"
        font_hl   = "'Inter', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
        font_body = "'Inter', system-ui, sans-serif"
    elif is_premium:
        font_url  = "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,600&family=Barlow:wght@400;500&display=swap"
        font_hl   = "'Cormorant Garamond', Georgia, serif"
        font_body = "'Barlow', sans-serif"
    else:
        font_url  = "https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,700;0,800;0,900;1,900&family=Barlow:wght@400;500&display=swap"
        font_hl   = "'Barlow Condensed', sans-serif"
        font_body = "'Barlow', sans-serif"

    # ── Layout dimensions ─────────────────────────────────────────────────────
    poster_h  = "760" if is_clean else "780"
    img_h     = "500" if is_clean else "560"
    hl_bottom = "172" if is_clean else "216"
    vb_h      = "330" if is_clean else "380"

    # ── Typography — weight / spacing / leading (tone-based) ─────────────────
    # Font size is resolved later, after headline lengths are known.
    if is_minimal:
        hl_weight, hl_spacing, _hl_lh_base = "700", "-0.025em", 0.93
    elif is_premium:
        hl_weight, hl_spacing, _hl_lh_base = "700", "0.01em",   1.05
    else:
        hl_weight, hl_spacing, _hl_lh_base = "900", "-0.03em",  0.87

    # Minimal: weight contrast (Apple-style); others: italic.
    # display:block is intentionally omitted — the <br> before .ha already
    # forces a new line, and removing it lets .hed.scrollWidth measure
    # the true pixel width of each line for the JS overflow fitter.
    ha_style = (
        f"color:#{accent};font-weight:300;font-style:normal;"
        if is_minimal else
        f"color:#{accent};font-style:italic;"
    )

    # ── Dynamic content ───────────────────────────────────────────────────────
    eyebrow_map = {
        "minimal":      "Introducing",
        "premium":      "Nouvelle Collection",
        "bold":         "New Season Drop",
        "friendly":     "Made for everyone",
        "professional": "Enterprise Edition",
    }
    eyebrow_text = eyebrow_map.get(tone, "New Arrival")
    # For professional brands, use the industry label as eyebrow if available
    if is_professional and industry:
        short = industry.split("&")[0].strip()
        if short and len(short) <= 24:
            eyebrow_text = short
    # Product category is most specific — use when provided (overrides tone defaults)
    if product_category:
        short_cat = product_category.split(",")[0].strip()
        if 3 <= len(short_cat) <= 30:
            eyebrow_text = short_cat

    badge_map = {
        "minimal":      "2026",
        "premium":      "Haute Couture",
        "bold":         "SS 2026",
        "friendly":     "New",
        "professional": "2026",
    }
    badge_text = badge_map.get(tone, "2026")

    side_right_map = {
        "minimal":      "INNOVATION",
        "premium":      "COLLECTION",
        "bold":         "ORIGINALS",
        "friendly":     "DISCOVER",
        "professional": "TECHNOLOGY",
    }
    side_right = side_right_map.get(tone, brand_name[:10].upper())

    # ── Headline copy ─────────────────────────────────────────────────────────
    if headlines:
        hl1 = headlines[0].upper().rstrip(".")
        hl2 = headlines[1].upper().rstrip(".") if len(headlines) > 1 else ""
    else:
        tagline_2 = taglines[1] if len(taglines) > 1 else (taglines[0] if taglines else "")
        words = tagline_2.upper().split()
        mid   = max(1, len(words) // 2)
        hl1   = " ".join(words[:mid])
        hl2   = " ".join(words[mid:]) if len(words) > mid else ""

    # Minimal: no trailing period (Apple-clean); bold: period for impact
    hl_period = "" if is_minimal else "."

    # ── Dynamic font size — prevents single-line overflow ─────────────────────
    # Uses conservative char-width multipliers per font family:
    #   Barlow Condensed ≈ 0.47×  (very narrow)
    #   Inter            ≈ 0.52×  (standard sans)
    #   Cormorant        ≈ 0.55×  (wide serif)
    # Available container width: 600px − 2×44px padding = 512px.
    # The JS fitter corrects any remaining overflow after actual font render.
    _longest = max(len(hl1), len(hl2) if hl2 else 0, 1)

    if is_minimal:
        # Inter: 512 / (0.52 × size) chars per line
        if _longest <= 12:   hl_size = "68px"
        elif _longest <= 16: hl_size = "60px"
        elif _longest <= 20: hl_size = "52px"
        elif _longest <= 25: hl_size = "44px"
        else:                hl_size = "38px"
    elif is_premium:
        # Cormorant Garamond: slightly wider per char
        if _longest <= 10:   hl_size = "74px"
        elif _longest <= 14: hl_size = "64px"
        elif _longest <= 18: hl_size = "54px"
        elif _longest <= 23: hl_size = "46px"
        else:                hl_size = "40px"
    else:
        # Barlow Condensed: very narrow — comfortably fits more chars/line
        if _longest <= 11:   hl_size = "86px"
        elif _longest <= 15: hl_size = "74px"
        elif _longest <= 19: hl_size = "62px"
        elif _longest <= 24: hl_size = "52px"
        elif _longest <= 28: hl_size = "44px"
        else:                hl_size = "38px"

    # Loosen line-height for smaller sizes — prevents descender/ascender clipping
    _fs_val = int(hl_size.rstrip("px"))
    if _fs_val < 50:
        hl_lh = "1.05"
    elif _fs_val < 62:
        hl_lh = str(round(_hl_lh_base + 0.07, 2))
    else:
        hl_lh = str(_hl_lh_base)

    # ── Subtitle — fills space below headline for minimal/premium ─────────────
    if is_minimal and taglines:
        sub_text = taglines[2] if len(taglines) > 2 else taglines[0]
        subtitle_html = f'<div class="sub">{sub_text[:72]}</div>'
    else:
        subtitle_html = ""

    # ── Ghost text ────────────────────────────────────────────────────────────
    ghost_src   = taglines[0].upper() if taglines else brand_name.upper()
    ghost_words = ghost_src.split()
    if len(ghost_words) < 2:
        ghost_words = [ghost_src, ghost_src]

    def ghost_row(offset: int, opacity: float, size: int, top: str, blur: int = 0) -> str:
        row_words = ghost_words[offset:] + ghost_words[:offset]
        text      = "  ".join(row_words * 5)
        blur_css  = f"filter:blur({blur}px);" if blur else ""
        return (
            f'<div class="gr" style="top:{top};font-size:{size}px;'
            f'opacity:{opacity};{blur_css}">{text}</div>'
        )

    if is_minimal:
        ghost_html = (
            ghost_row(0, 0.018, 88,  "2%",  0) +
            ghost_row(1, 0.022, 104, "18%", 0) +
            ghost_row(0, 0.014, 94,  "36%", 1) +
            ghost_row(1, 0.010, 80,  "54%", 2) +
            ghost_row(0, 0.007, 70,  "70%", 3)
        )
    else:
        ghost_html = (
            ghost_row(0, 0.04,  100, "2%",  0) +
            ghost_row(1, 0.055, 118, "18%", 0) +
            ghost_row(0, 0.038, 106, "36%", 1) +
            ghost_row(1, 0.028,  90, "54%", 2) +
            ghost_row(0, 0.018,  78, "70%", 3)
        )

    # ── Feature tags ──────────────────────────────────────────────────────────
    feat1 = key_features[0][:28] if key_features else "Performance"
    feat2 = key_features[1][:28] if len(key_features) > 1 else "Premium Craft"
    feat3 = key_features[2][:28] if len(key_features) > 2 else "Built to Last"

    cta_btn   = cta_line[:24] if cta_line else ("Shop" if is_minimal else "Shop Now")
    side_left = display_name[:16].upper()

    # ── Logo HTML ─────────────────────────────────────────────────────────────
    if logo_url and (logo_url.startswith("http") or logo_url.startswith("data:")):
        if is_clean:
            # Invert to white — clean on dark background, no white pill needed
            logo_style = "height:30px;width:auto;max-width:130px;object-fit:contain;filter:brightness(0) invert(1);"
        else:
            logo_style = "height:36px;width:auto;max-width:140px;object-fit:contain;background:rgba(255,255,255,0.93);padding:5px 10px;border-radius:3px;"
        logo_html = (
            f'<img src="{logo_url}" alt="{display_name}" style="{logo_style}" '
            f'onerror="this.style.display=\'none\';'
            f'document.querySelector(\'.logo-text\').style.display=\'block\'">'
        )
        logo_text_css = "display:none"
    else:
        # No external logo — generate an SVG mark from brand name + tone
        logo_html     = generate_svg_logo(display_name, tone, f"#{accent}")
        logo_text_css = "display:none"

    # ── Image grid ─────────────────────────────────────────────────────────────
    def img_tag(src: str, label: str) -> str:
        if src:
            return (
                f'<img class="gi" src="{src}" alt="{label}" '
                f'onerror="this.parentElement.style.background=\'#181818\';this.remove()">'
            )
        return ""

    img0 = product_images[0] if len(product_images) > 0 else ""
    img1 = product_images[1] if len(product_images) > 1 else ""
    img2 = product_images[2] if len(product_images) > 2 else ""

    if any([img0, img1, img2]):
        grid_html = (
            f'<div class="ig">'
            f'  <div class="gm">{img_tag(img0, display_name)}</div>'
            f'  <div class="gs">'
            f'    <div class="gt">{img_tag(img1, display_name)}</div>'
            f'    <div class="gt">{img_tag(img2, display_name)}</div>'
            f'  </div>'
            f'  <div class="vl"></div>'
            f'  <div class="vr"></div>'
            f'  <div class="vt"></div>'
            f'  <div class="vb"></div>'
            f'</div>'
        )
    else:
        # No product images — tone-aware abstract visual with hero product render
        _vis_cat   = _infer_visual_category(product_category, industry)
        _prod_html = generate_product_visual(_vis_cat, f"#{accent}", tone) if _vis_cat else ""
        grid_html  = _abstract_visual(tone, primary_color, f"#{accent}", int(img_h), _prod_html)

    # ── Tone-specific CSS details ─────────────────────────────────────────────
    tag_radius  = "20px" if is_minimal else ("4px" if is_premium else "0")
    cta_clip    = ""     if is_clean   else "clip-path:polygon(0 0,calc(100% - 10px) 0,100% 10px,100% 100%,0 100%);"
    corner_html = ""     if is_clean   else '<div class="corner"></div>'
    abar_html   = ""     if is_minimal else '<div class="abar"></div>'

    eb_line_opacity = "30" if is_clean else "66"

    if is_minimal:
        glow_bg = f"radial-gradient(circle,rgba(255,255,255,0.04) 0%,#{accent}10 40%,transparent 68%)"
    elif is_premium:
        glow_bg = f"radial-gradient(circle,#{accent}18 0%,#{accent}08 42%,transparent 65%)"
    else:
        glow_bg = f"radial-gradient(circle,#{accent}2a 0%,#{accent}0d 35%,transparent 65%)"

    logo_text_size    = "24px" if is_clean else "30px"
    logo_text_spacing = "0.04em" if is_minimal else "0.07em"
    logo_font_weight  = "700"   if is_clean  else "900"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link href="{font_url}" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#030303;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:{font_body}}}

/* ── POSTER SHELL ── */
.poster{{
  position:relative;width:600px;height:{poster_h}px;
  background:#0a0a0a;overflow:hidden;
}}

/* ── GHOST TEXT ── */
.ghost{{position:absolute;inset:0;overflow:hidden;z-index:1;pointer-events:none}}
.gr{{
  position:absolute;left:-30px;right:-30px;white-space:nowrap;
  font-family:{font_hl};font-weight:{hl_weight};
  text-transform:uppercase;letter-spacing:{hl_spacing};line-height:1;
  color:#{ghost_color};user-select:none;
}}

/* ── IMAGE GRID — full bleed ── */
.ig{{
  position:absolute;top:0;left:0;right:0;height:{img_h}px;
  z-index:3;display:flex;gap:3px;overflow:hidden;
}}
.gm{{flex:0 0 62%;overflow:hidden;background:#181818}}
.gs{{flex:1;display:flex;flex-direction:column;gap:3px}}
.gt{{flex:1;overflow:hidden;background:#181818}}
.gi{{width:100%;height:100%;object-fit:cover;display:block}}

/* ── CINEMATIC VIGNETTES ── */
.vl{{position:absolute;top:0;bottom:0;left:0;width:130px;
  background:linear-gradient(to right,#0a0a0a 0%,transparent 100%);z-index:4;pointer-events:none}}
.vr{{position:absolute;top:0;bottom:0;right:0;width:70px;
  background:linear-gradient(to left,#0a0a0a 0%,transparent 100%);z-index:4;pointer-events:none}}
.vt{{position:absolute;top:0;left:0;right:0;height:110px;
  background:linear-gradient(to bottom,#0a0a0a 0%,transparent 100%);z-index:4;pointer-events:none}}
.vb{{
  position:absolute;bottom:0;left:0;right:0;height:{vb_h}px;
  background:linear-gradient(
    to top,
    #0a0a0a 0%,#0a0a0a 14%,
    rgba(10,10,10,0.96) 32%,rgba(10,10,10,0.78) 52%,
    rgba(10,10,10,0.35) 72%,transparent 100%
  );
  z-index:5;pointer-events:none;
}}

/* ── GLOW ── */
.glow{{
  position:absolute;width:520px;height:520px;border-radius:50%;
  background:{glow_bg};
  bottom:80px;left:50%;transform:translateX(-50%);
  z-index:6;pointer-events:none;
}}

/* ── CORNER ── */
.corner{{position:absolute;top:0;right:0;
  border-left:80px solid transparent;border-top:80px solid #{accent}2a;z-index:4}}

/* ── TOPBAR ── */
.topbar{{
  position:absolute;top:0;left:0;right:0;padding:22px 44px;
  display:flex;align-items:center;justify-content:space-between;z-index:9;
}}
.logo-wrap{{display:flex;align-items:center;gap:10px}}
.logo-text{{
  font-family:{font_hl};font-weight:{logo_font_weight};
  font-size:{logo_text_size};letter-spacing:{logo_text_spacing};
  color:#fff;text-transform:uppercase;{logo_text_css}
}}
.badge{{
  font-family:{font_body};font-size:9px;font-weight:600;
  letter-spacing:0.32em;text-transform:uppercase;
  color:rgba(255,255,255,0.22);border:1px solid rgba(255,255,255,0.07);padding:5px 13px;
}}
.abar{{position:absolute;left:44px;top:76px;width:48px;height:2px;background:#{accent};z-index:9}}

/* ── SIDE TEXT ── */
.side{{position:absolute;top:0;bottom:0;display:flex;align-items:center;z-index:8}}
.side span{{
  writing-mode:vertical-rl;font-family:{font_body};font-weight:600;
  font-size:8px;letter-spacing:0.44em;text-transform:uppercase;
  color:rgba(255,255,255,0.08);
}}
.sl{{left:12px}}
.sr{{right:12px;transform:rotate(180deg)}}

/* ── HEADLINE ── */
.hl{{position:absolute;bottom:{hl_bottom}px;left:44px;right:44px;z-index:8;}}
.eyebrow{{
  font-family:{font_body};font-size:9.5px;font-weight:600;
  letter-spacing:0.42em;text-transform:uppercase;color:#{accent};
  margin-bottom:14px;display:flex;align-items:center;gap:12px;opacity:0.9;
}}
.eyebrow::after{{content:'';flex:1;height:1px;
  background:linear-gradient(to right,#{accent}{eb_line_opacity},transparent)}}
.hed{{
  font-family:{font_hl};font-weight:{hl_weight};
  font-size:{hl_size};line-height:{hl_lh};
  color:#fff;text-transform:uppercase;letter-spacing:{hl_spacing};
  text-shadow:0 4px 40px rgba(0,0,0,0.6);
  white-space:nowrap;
}}
.hed .ha{{ {ha_style} }}
.sub{{
  font-family:{font_body};font-size:13px;font-weight:300;
  color:rgba(255,255,255,0.44);margin-top:18px;
  letter-spacing:0.02em;line-height:1.55;max-width:360px;
}}

/* ── BOTTOM CONTENT ── */
.bot{{
  position:absolute;bottom:0;left:0;right:0;padding:0 44px 22px;z-index:9;
  background:linear-gradient(to top,#0a0a0a 0%,rgba(10,10,10,0.98) 55%,transparent 100%);
}}
.rule{{width:100%;height:1px;background:rgba(255,255,255,0.06);margin-bottom:12px}}
.tags{{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}}
.tag{{
  font-family:{font_body};font-size:8.5px;font-weight:600;
  letter-spacing:0.14em;text-transform:uppercase;padding:5px 12px;border-radius:{tag_radius};
}}
.ta{{color:#{accent};border:1px solid #{accent}44;background:#{accent}0d}}
.to{{color:rgba(255,255,255,0.30);border:1px solid rgba(255,255,255,0.09)}}
.brow{{display:flex;align-items:center;justify-content:space-between}}
.cta{{
  font-family:{font_body};font-weight:700;font-size:11px;
  letter-spacing:0.22em;text-transform:uppercase;
  color:#{accent_text};background:#{accent};
  border:none;padding:12px 32px;text-decoration:none;display:inline-block;cursor:pointer;
  {cta_clip}
}}
</style>
</head>
<body>
<div class="poster">

  <div class="ghost">{ghost_html}</div>
  {grid_html}
  <div class="glow"></div>
  {corner_html}

  <div class="side sl"><span>{side_left}</span></div>
  <div class="side sr"><span>{side_right}</span></div>

  <div class="topbar">
    <div class="logo-wrap">
      {logo_html}
      <div class="logo-text">{display_name[:12]}</div>
    </div>
    <div class="badge">{badge_text}</div>
  </div>
  {abar_html}

  <div class="hl">
    <div class="eyebrow">{eyebrow_text}</div>
    <div class="hed">
      {hl1}{hl_period}<br>
      <span class="ha">{hl2 or hl1}{hl_period}</span>
    </div>
    {subtitle_html}
  </div>

  <div class="bot">
    <div class="rule"></div>
    <div class="tags">
      <span class="tag ta">{feat1}</span>
      <span class="tag to">{feat2}</span>
      <span class="tag to">{feat3}</span>
    </div>
    <div class="brow">
      <a class="cta" href="#">{cta_btn}</a>
    </div>
  </div>

</div>
<script>
(function(){{
  /* Headline overflow fitter.
     white-space:nowrap on .hed means each line won't soft-wrap.
     If scrollWidth > offsetWidth, at least one line overflows the
     512px container — reduce font-size in 2px steps until it fits. */
  function fit(){{
    var h=document.querySelector('.hed');
    if(!h)return;
    var minFs=24, maxSteps=30;
    for(var i=0;i<maxSteps;i++){{
      if(h.scrollWidth<=h.offsetWidth)break;
      var fs=parseFloat(window.getComputedStyle(h).fontSize);
      if(isNaN(fs)||fs<=minFs)break;
      h.style.fontSize=(fs-2)+'px';
    }}
  }}
  /* Run after webfonts are ready; setTimeout covers iframe timing gaps. */
  if(document.fonts&&document.fonts.ready){{document.fonts.ready.then(fit);}}
  else{{window.addEventListener('load',fit);}}
  setTimeout(fit,300);
  setTimeout(fit,800);
}})();
</script>
</body>
</html>"""


# ── Color Utilities ───────────────────────────────────────────────────────────

def _lighten(hex_color: str, factor: float = 1.4) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "ffffff"
    try:
        r = min(255, int(int(hex_color[0:2], 16) * factor))
        g = min(255, int(int(hex_color[2:4], 16) * factor))
        b = min(255, int(int(hex_color[4:6], 16) * factor))
        return f"{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "ffffff"


def _is_dark(hex_color: str) -> bool:
    hex_color = hex_color.lstrip("#")
    try:
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 0.4
    except Exception:
        return True


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )


def generate_svg_logo(name: str, tone: str, accent_hex: str) -> str:
    """
    Generates inline SVG markup for a clean brand logo mark.
    The mark shape and typography vary by tone:
      minimal      — concentric rings (precision / Apple-like)
      premium      — diamond monogram (editorial / Dior-like)
      bold         — dual chevrons (kinetic / Nike-like)
      friendly     — filled circle badge
      professional — filled square badge
    """
    accent = accent_hex.lstrip("#")
    label  = _xml_escape(name[:14].upper())

    if tone == "minimal":
        # Thin ring + dot — precision aesthetics
        char_w, text_x, fw, fs, ls, ty = 8.5, 30, "700", "15", "-0.01em", "19.5"
        font = "Inter,system-ui,-apple-system,Helvetica,sans-serif"
        mark = (
            f'<circle cx="14" cy="14" r="10" fill="none" stroke="#{accent}" stroke-width="1.5"/>'
            f'<circle cx="14" cy="14" r="3.5" fill="#{accent}"/>'
        )

    elif tone == "premium":
        # Diamond cross — editorial luxury
        char_w, text_x, fw, fs, ls, ty = 9.3, 32, "700", "15", "0.12em", "20"
        font = "'Cormorant Garamond',Georgia,'Times New Roman',serif"
        mark = (
            f'<polygon points="14,2 25,14 14,26 3,14" fill="none" stroke="#{accent}" stroke-width="1.2"/>'
            f'<line x1="14" y1="8" x2="14" y2="20" stroke="#{accent}" stroke-width="0.8" stroke-opacity="0.6"/>'
            f'<line x1="8" y1="14" x2="20" y2="14" stroke="#{accent}" stroke-width="0.8" stroke-opacity="0.6"/>'
        )

    elif tone == "bold":
        # Dual chevrons — kinetic energy
        char_w, text_x, fw, fs, ls, ty = 11, 30, "900", "20", "0.04em", "22"
        font = "'Barlow Condensed',Impact,'Arial Narrow',sans-serif"
        mark = (
            f'<polygon points="0,28 9,0 15,0 6,28" fill="#{accent}"/>'
            f'<polygon points="10,28 19,0 23,0 14,28" fill="#{accent}" fill-opacity="0.45"/>'
        )

    elif tone == "friendly":
        # Filled circle with initials
        char_w, text_x, fw, fs, ls, ty = 9, 32, "700", "15", "0.04em", "20"
        font = "'Barlow',sans-serif"
        initials = _xml_escape(name[:2].upper()) if len(name) >= 2 else _xml_escape(name[:1].upper())
        mark = (
            f'<circle cx="14" cy="14" r="13" fill="#{accent}"/>'
            f'<text x="14" y="19.5" text-anchor="middle" font-family="\'Barlow Condensed\',sans-serif" '
            f'font-weight="900" font-size="13" fill="white">{initials}</text>'
        )

    else:  # professional / default
        # Filled square badge with initials
        char_w, text_x, fw, fs, ls, ty = 8, 36, "700", "14", "0.07em", "20"
        font = "Inter,system-ui,sans-serif"
        initials = _xml_escape(name[:2].upper()) if len(name) >= 2 else _xml_escape(name[:1].upper())
        mark = (
            f'<rect x="0" y="1" width="28" height="26" fill="#{accent}" rx="3"/>'
            f'<text x="14" y="19.5" text-anchor="middle" font-family="Inter,system-ui,sans-serif" '
            f'font-weight="800" font-size="13" fill="white">{initials}</text>'
        )

    total_w = int(text_x + len(label) * char_w + 8)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="28" viewBox="0 0 {total_w} 28">'
        f'{mark}'
        f'<text x="{text_x}" y="{ty}" font-family="{font}" font-weight="{fw}" '
        f'font-size="{fs}" fill="white" letter-spacing="{ls}">{label}</text>'
        f'</svg>'
    )


def _abstract_visual(tone: str, primary_hex: str, accent_hex: str, img_h: int, product_html: str = "") -> str:
    """
    Generates an HTML string for the poster image area when no product photos are available.
    Returns a <div class="ig"> with a tone-aware SVG geometric visual inside it.
    The .ig CSS class supplies correct positioning and height.
    """
    p = primary_hex.lstrip("#")
    a = accent_hex.lstrip("#")
    h = img_h

    vignettes = (
        '<div class="vl"></div>'
        '<div class="vr"></div>'
        '<div class="vt"></div>'
        '<div class="vb"></div>'
    )

    if tone == "minimal":
        # Concentric rings — Apple/Tesla precision
        bg = f"linear-gradient(150deg,#030305 0%,#07070f 40%,#{p}12 65%,#030305 100%)"
        rings = "".join(
            f'<circle cx="300" cy="{h//2}" r="{r}" fill="none" '
            f'stroke="#{a}" stroke-width="0.7" stroke-opacity="{op:.2f}"/>'
            for r, op in [(270, 0.12), (210, 0.10), (155, 0.09), (105, 0.08), (62, 0.07), (25, 0.06)]
        )
        inner = (
            f'<defs><radialGradient id="av-rg" cx="50%" cy="50%" r="55%">'
            f'<stop offset="0%" stop-color="#{a}" stop-opacity="0.20"/>'
            f'<stop offset="100%" stop-color="#{a}" stop-opacity="0"/>'
            f'</radialGradient></defs>'
            f'<rect width="600" height="{h}" fill="url(#av-rg)"/>'
            + rings
        )

    elif tone == "premium":
        # Diagonal editorial light leak
        bg = f"linear-gradient(160deg,#0a0806 0%,#100d08 40%,#{p}18 70%,#0a0806 100%)"
        inner = (
            f'<defs><linearGradient id="av-lg" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" stop-color="#{a}" stop-opacity="0"/>'
            f'<stop offset="42%" stop-color="#{a}" stop-opacity="0.22"/>'
            f'<stop offset="58%" stop-color="#{a}" stop-opacity="0.18"/>'
            f'<stop offset="100%" stop-color="#{a}" stop-opacity="0"/>'
            f'</linearGradient></defs>'
            f'<rect width="600" height="{h}" fill="url(#av-lg)"/>'
            f'<line x1="0" y1="{h}" x2="600" y2="0" stroke="#{a}" stroke-width="0.6" stroke-opacity="0.18"/>'
            f'<line x1="80" y1="{h}" x2="600" y2="80" stroke="#{a}" stroke-width="0.3" stroke-opacity="0.11"/>'
            f'<line x1="0" y1="{h-80}" x2="520" y2="0" stroke="#{a}" stroke-width="0.3" stroke-opacity="0.08"/>'
        )

    elif tone == "bold":
        # Angular slash — kinetic energy
        bg = f"linear-gradient(118deg,#030303 0%,#080808 30%,#{p}30 62%,#{a}20 100%)"
        inner = (
            f'<polygon points="360,0 600,0 600,{h} 140,{h}" fill="#{a}" fill-opacity="0.11"/>'
            f'<polygon points="440,0 600,0 600,{h//2}" fill="#{a}" fill-opacity="0.08"/>'
            f'<line x1="360" y1="0" x2="140" y2="{h}" stroke="#{a}" stroke-width="1.2" stroke-opacity="0.22"/>'
            f'<line x1="440" y1="0" x2="220" y2="{h}" stroke="#{a}" stroke-width="0.6" stroke-opacity="0.14"/>'
            f'<line x1="520" y1="0" x2="300" y2="{h}" stroke="#{a}" stroke-width="0.4" stroke-opacity="0.09"/>'
        )

    elif tone == "friendly":
        # Warm playful circles
        bg = f"linear-gradient(135deg,#060608 0%,#0a0a12 40%,#{p}22 70%,#060608 100%)"
        inner = (
            f'<defs><radialGradient id="av-rg2" cx="75%" cy="25%" r="48%">'
            f'<stop offset="0%" stop-color="#{a}" stop-opacity="0.26"/>'
            f'<stop offset="100%" stop-color="#{a}" stop-opacity="0"/>'
            f'</radialGradient></defs>'
            f'<rect width="600" height="{h}" fill="url(#av-rg2)"/>'
            f'<circle cx="480" cy="90" r="220" fill="#{a}" fill-opacity="0.07"/>'
            f'<circle cx="110" cy="{h-80}" r="170" fill="#{p}" fill-opacity="0.06"/>'
        )

    else:  # professional / default
        # Grid lines + concentric circles — enterprise precision
        bg = f"linear-gradient(140deg,#030308 0%,#06060e 40%,#{p}16 70%,#030308 100%)"
        v_lines = "".join(
            f'<line x1="{i*60}" y1="0" x2="{i*60}" y2="{h}" '
            f'stroke="#{a}" stroke-width="0.4" stroke-opacity="0.22"/>'
            for i in range(11)
        )
        h_lines = "".join(
            f'<line x1="0" y1="{i*55}" x2="600" y2="{i*55}" '
            f'stroke="#{a}" stroke-width="0.4" stroke-opacity="0.22"/>'
            for i in range(h // 55 + 1)
        )
        inner = (
            f'<defs><radialGradient id="av-rg3" cx="50%" cy="50%" r="52%">'
            f'<stop offset="0%" stop-color="#{a}" stop-opacity="0.18"/>'
            f'<stop offset="100%" stop-color="#{a}" stop-opacity="0"/>'
            f'</radialGradient></defs>'
            f'<rect width="600" height="{h}" fill="url(#av-rg3)"/>'
            + v_lines + h_lines +
            f'<circle cx="300" cy="{h//2}" r="210" fill="none" stroke="#{a}" stroke-width="0.7" stroke-opacity="0.28"/>'
            f'<circle cx="300" cy="{h//2}" r="130" fill="none" stroke="#{a}" stroke-width="0.5" stroke-opacity="0.22"/>'
        )

    svg = (
        f'<svg width="600" height="{h}" viewBox="0 0 600 {h}" '
        f'style="position:absolute;inset:0;z-index:1;" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'{inner}'
        f'</svg>'
    )
    return f'<div class="ig" style="background:{bg};">{svg}{product_html}{vignettes}</div>'


# ── Industry-aware product visual system ──────────────────────────────────────

def _infer_visual_category(product_category: str, industry: str) -> str:
    """
    Maps product_category + industry keywords to a visual template name.
    Returns one of: "skincare", "fitness", "technology", "fashion", "beverage", or "".
    """
    # product_category is the primary signal; industry is used as tiebreaker only
    pc   = product_category.lower()
    text = (product_category + " " + industry).lower()

    if any(w in text for w in [
        "skincare", "serum", "moisturizer", "beauty", "cosmetic",
        "fragrance", "perfume", "lotion", "cream", "sunscreen",
        "toner", "essence", "retinol",
    ]):
        return "skincare"

    # Fitness: check product_category ONLY — industry might contain "extreme sports"
    # for energy drinks, which should still map to beverage.
    if any(w in pc for w in [
        "fitness", "sport", "running", "athletic", "workout", "training",
        "gym", "sneaker", "shoe", "footwear", "exercise", "nutrition",
    ]):
        return "fitness"

    if any(w in text for w in [
        "tech", "software", "hardware", "cloud", "ai ", " ai", "device",
        "phone", "laptop", "computer", "wireless", "headphone", "audio",
        "electronic", "digital", "wearable", "smart",
    ]):
        return "technology"

    if any(w in text for w in [
        "food", "beverage", "drink", "coffee", "tea", "juice", "energy",
        "soda", "beer", "wine", "water", "cafe", "restaurant", "brew", "spirits",
    ]):
        return "beverage"

    # fashion last — broad catch-all for luxury / apparel / accessories
    if any(w in text for w in [
        "fashion", "luxury", "couture", "apparel", "wear", "clothing",
        "handbag", "bag", "jewel", "accessory", "watch", "haute",
    ]):
        return "fashion"

    # fitness secondary: sport-related industry with no better category match
    if any(w in text for w in ["sport", "athletic", "fitness"]):
        return "fitness"

    return ""


def _product_skincare(accent: str) -> str:
    """SVG: tall serum dropper bottle — La Mer / Tatcha aesthetic."""
    a = accent.lstrip("#")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="320" viewBox="0 0 150 320">'
        # ground shadow
        f'<ellipse cx="75" cy="313" rx="46" ry="6" fill="#000" fill-opacity="0.55"/>'
        # reflection ghost
        f'<g transform="translate(0,620) scale(1,-1)" opacity="0.08">'
        f'<path d="M30,100 Q30,78 75,78 Q120,78 120,100 L120,300 Q120,314 75,314 Q30,314 30,300 Z" fill="#{a}"/>'
        f'</g>'
        # bottle body — gently rounded rectangle
        f'<path d="M30,100 Q30,78 75,78 Q120,78 120,100 L120,300 Q120,314 75,314 Q30,314 30,300 Z"'
        f' fill="#{a}15" stroke="#{a}" stroke-width="1.1" stroke-opacity="0.62"/>'
        # left glass specular highlight
        f'<path d="M38,106 Q38,86 46,82 L46,298 Q42,308 38,302 Z" fill="white" fill-opacity="0.07"/>'
        # right edge glint
        f'<line x1="116" y1="105" x2="116" y2="295" stroke="white" stroke-width="1" stroke-opacity="0.04"/>'
        # label band
        f'<rect x="36" y="162" width="78" height="92" rx="3" fill="#{a}1e" stroke="#{a}55" stroke-width="0.8"/>'
        # label identity lines
        f'<line x1="48" y1="183" x2="102" y2="183" stroke="#{a}" stroke-width="0.9" stroke-opacity="0.85"/>'
        f'<line x1="54" y1="197" x2="96" y2="197" stroke="#{a}" stroke-width="0.6" stroke-opacity="0.60"/>'
        f'<line x1="50" y1="210" x2="100" y2="210" stroke="#{a}" stroke-width="0.6" stroke-opacity="0.50"/>'
        f'<line x1="56" y1="222" x2="94" y2="222" stroke="#{a}" stroke-width="0.5" stroke-opacity="0.38"/>'
        f'<line x1="52" y1="234" x2="98" y2="234" stroke="#{a}" stroke-width="0.5" stroke-opacity="0.30"/>'
        # neck
        f'<path d="M60,50 L60,80 L90,80 L90,50 Q90,44 75,44 Q60,44 60,50 Z"'
        f' fill="#{a}28" stroke="#{a}" stroke-width="1" stroke-opacity="0.70"/>'
        # shoulder curve
        f'<path d="M30,82 Q30,70 60,66 L90,66 Q120,70 120,82 L120,100 L30,100 Z"'
        f' fill="#{a}22" stroke="#{a}" stroke-width="0.8" stroke-opacity="0.55"/>'
        # dropper rubber bulb
        f'<ellipse cx="75" cy="32" rx="12" ry="15" fill="#{a}50" stroke="#{a}" stroke-width="0.9"/>'
        f'<line x1="75" y1="18" x2="75" y2="45" stroke="#{a}aa" stroke-width="0.6"/>'
        f'<line x1="75" y1="44" x2="75" y2="50" stroke="#{a}" stroke-width="2" stroke-opacity="0.5"/>'
        # bulb highlight
        f'<ellipse cx="70" cy="25" rx="3" ry="5" fill="white" fill-opacity="0.20"/>'
        f'</svg>'
    )


def _product_fitness(accent: str) -> str:
    """SVG: athletic water bottle — Hydro Flask / Stanley aesthetic."""
    a = accent.lstrip("#")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="122" height="310" viewBox="0 0 122 310">'
        # ground shadow
        f'<ellipse cx="61" cy="303" rx="37" ry="5" fill="#000" fill-opacity="0.55"/>'
        # reflection ghost
        f'<g transform="translate(0,604) scale(1,-1)" opacity="0.07">'
        f'<path d="M16,80 Q16,60 61,60 Q106,60 106,80 L110,162 Q110,204 106,214 L106,286 Q106,297 61,297 Q16,297 16,286 L16,214 Q12,204 12,162 Z" fill="#{a}"/>'
        f'</g>'
        # bottle body — waist-narrowed for grip ergonomics
        f'<path d="M16,80 Q16,60 61,60 Q106,60 106,80 L110,162 Q110,204 106,214 L106,286 Q106,297 61,297 Q16,297 16,286 L16,214 Q12,204 12,162 Z"'
        f' fill="#{a}22" stroke="#{a}" stroke-width="1.2" stroke-opacity="0.70"/>'
        # waist grip indent lines
        f'<line x1="20" y1="168" x2="102" y2="168" stroke="#{a}88" stroke-width="1.0" stroke-opacity="0.32"/>'
        f'<line x1="20" y1="181" x2="102" y2="181" stroke="#{a}88" stroke-width="1.0" stroke-opacity="0.32"/>'
        f'<line x1="20" y1="194" x2="102" y2="194" stroke="#{a}88" stroke-width="1.0" stroke-opacity="0.32"/>'
        # brand medallion
        f'<circle cx="61" cy="118" r="26" fill="#{a}20" stroke="#{a}55" stroke-width="0.8"/>'
        f'<circle cx="61" cy="118" r="17" fill="#{a}30" stroke="#{a}66" stroke-width="0.7"/>'
        # left body highlight
        f'<path d="M24,84 Q24,66 30,62 L30,283 Q26,291 24,286 Z" fill="white" fill-opacity="0.08"/>'
        # cap neck cylinder
        f'<rect x="43" y="30" width="36" height="32" rx="8" fill="#{a}40" stroke="#{a}90" stroke-width="1"/>'
        # cap lid
        f'<path d="M37,12 Q37,4 61,4 Q85,4 85,12 L85,32 L37,32 Z" fill="#{a}75" stroke="#{a}" stroke-width="1"/>'
        # spout nub
        f'<rect x="55" y="2" width="12" height="12" rx="4" fill="#{a}" stroke="#{a}" stroke-width="0.6"/>'
        f'</svg>'
    )


def _product_technology(accent: str) -> str:
    """SVG: over-ear wireless headphones — AirPods Max / Sony XM5 aesthetic."""
    a = accent.lstrip("#")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="272" height="238" viewBox="0 0 272 238">'
        # ground shadow
        f'<ellipse cx="136" cy="231" rx="90" ry="7" fill="#000" fill-opacity="0.50"/>'
        # headband arc — main stroke
        f'<path d="M44,150 Q44,34 136,34 Q228,34 228,150"'
        f' fill="none" stroke="#{a}" stroke-width="17" stroke-linecap="round" stroke-opacity="0.85"/>'
        # headband inner highlight streak
        f'<path d="M56,150 Q56,50 136,50 Q216,50 216,150"'
        f' fill="none" stroke="white" stroke-width="4" stroke-linecap="round" stroke-opacity="0.09"/>'
        # left adjustment arm
        f'<line x1="44" y1="132" x2="44" y2="150" stroke="#{a}cc" stroke-width="11" stroke-linecap="round"/>'
        # right adjustment arm
        f'<line x1="228" y1="132" x2="228" y2="150" stroke="#{a}cc" stroke-width="11" stroke-linecap="round"/>'
        # ── left ear cup ──
        # outer shell
        f'<ellipse cx="44" cy="165" rx="34" ry="40" fill="#{a}28" stroke="#{a}" stroke-width="1.5"/>'
        # cushion ring
        f'<ellipse cx="44" cy="165" rx="24" ry="29" fill="#{a}45" stroke="#{a}88" stroke-width="1"/>'
        # driver dome
        f'<ellipse cx="44" cy="165" rx="12" ry="14" fill="#{a}" fill-opacity="0.80"/>'
        # cup specular
        f'<ellipse cx="37" cy="153" rx="5" ry="7" fill="white" fill-opacity="0.14"/>'
        # ── right ear cup ──
        f'<ellipse cx="228" cy="165" rx="34" ry="40" fill="#{a}28" stroke="#{a}" stroke-width="1.5"/>'
        f'<ellipse cx="228" cy="165" rx="24" ry="29" fill="#{a}45" stroke="#{a}88" stroke-width="1"/>'
        f'<ellipse cx="228" cy="165" rx="12" ry="14" fill="#{a}" fill-opacity="0.80"/>'
        f'<ellipse cx="221" cy="153" rx="5" ry="7" fill="white" fill-opacity="0.14"/>'
        # USB-C port detail
        f'<rect x="16" y="196" width="10" height="4" rx="2" fill="#{a}cc"/>'
        f'</svg>'
    )


def _product_fashion(accent: str) -> str:
    """SVG: rectangular glass perfume bottle — Chanel No.5 / Dior J'adore aesthetic."""
    a = accent.lstrip("#")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="142" height="292" viewBox="0 0 142 292">'
        # ground shadow
        f'<ellipse cx="71" cy="285" rx="44" ry="6" fill="#000" fill-opacity="0.50"/>'
        # reflection ghost
        f'<g transform="translate(0,568) scale(1,-1)" opacity="0.07">'
        f'<path d="M18,96 L18,260 Q18,276 71,276 Q124,276 124,260 L124,96 Z" fill="#{a}"/>'
        f'</g>'
        # bottle body — flat-sided glass rectangle
        f'<path d="M18,96 L18,260 Q18,276 71,276 Q124,276 124,260 L124,96 Z"'
        f' fill="#{a}18" stroke="#{a}80" stroke-width="1.2"/>'
        # left beveled edge
        f'<line x1="32" y1="96" x2="32" y2="260" stroke="#{a}55" stroke-width="0.8"/>'
        # right beveled edge
        f'<line x1="110" y1="96" x2="110" y2="260" stroke="#{a}55" stroke-width="0.8"/>'
        # left glass specular band
        f'<path d="M22,100 L22,258 Q20,266 18,260 L18,100 Z" fill="white" fill-opacity="0.07"/>'
        # decorative band top rule
        f'<rect x="18" y="148" width="106" height="3" fill="#{a}" fill-opacity="0.55"/>'
        # decorative band thin rule
        f'<rect x="18" y="156" width="106" height="1.5" fill="#{a}" fill-opacity="0.35"/>'
        # label zone
        f'<rect x="26" y="166" width="90" height="72" rx="2" fill="#{a}18" stroke="#{a}44" stroke-width="0.8"/>'
        # label lines
        f'<line x1="36" y1="187" x2="106" y2="187" stroke="#{a}" stroke-width="0.9" stroke-opacity="0.82"/>'
        f'<line x1="42" y1="201" x2="100" y2="201" stroke="#{a}" stroke-width="0.6" stroke-opacity="0.58"/>'
        f'<line x1="38" y1="214" x2="104" y2="214" stroke="#{a}" stroke-width="0.6" stroke-opacity="0.46"/>'
        f'<line x1="44" y1="226" x2="98" y2="226" stroke="#{a}" stroke-width="0.5" stroke-opacity="0.35"/>'
        # neck / shoulder
        f'<path d="M18,80 Q18,66 44,62 L44,46 L98,46 L98,62 Q124,66 124,80 L124,96 L18,96 Z"'
        f' fill="#{a}28" stroke="#{a}80" stroke-width="1"/>'
        # stopper cap
        f'<path d="M40,10 Q40,2 71,2 Q102,2 102,10 L102,48 L40,48 Z"'
        f' fill="#{a}80" stroke="#{a}" stroke-width="1"/>'
        # cap left highlight
        f'<path d="M44,12 L44,46 L48,46 L48,10 Q48,6 44,8 Z" fill="white" fill-opacity="0.10"/>'
        # atomizer pump
        f'<circle cx="116" cy="30" r="8" fill="#{a}45" stroke="#{a}88" stroke-width="0.8"/>'
        f'<line x1="102" y1="30" x2="108" y2="30" stroke="#{a}" stroke-width="1.5"/>'
        f'</svg>'
    )


def _product_beverage(accent: str) -> str:
    """SVG: slim energy drink can — Red Bull / Monster aesthetic."""
    a = accent.lstrip("#")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="122" height="282" viewBox="0 0 122 282">'
        # ground shadow
        f'<ellipse cx="61" cy="275" rx="39" ry="6" fill="#000" fill-opacity="0.55"/>'
        # reflection ghost
        f'<g transform="translate(0,550) scale(1,-1)" opacity="0.07">'
        f'<path d="M17,268 L17,68 Q17,56 61,56 Q105,56 105,68 L105,268 Q105,276 61,276 Q17,276 17,268 Z" fill="#{a}"/>'
        f'</g>'
        # can body
        f'<path d="M17,68 L17,268 Q17,276 61,276 Q105,276 105,268 L105,68 Z"'
        f' fill="#{a}22" stroke="#{a}88" stroke-width="1.3" stroke-opacity="0.70"/>'
        # top ellipse
        f'<ellipse cx="61" cy="68" rx="44" ry="9" fill="#{a}40" stroke="#{a}88" stroke-width="1"/>'
        # bottom ellipse
        f'<ellipse cx="61" cy="268" rx="44" ry="8" fill="#{a}30" stroke="#{a}88" stroke-width="1"/>'
        # left highlight stripe
        f'<path d="M25,72 L25,262 Q23,270 19,268 L19,70 Z" fill="white" fill-opacity="0.08"/>'
        # label top rule
        f'<line x1="17" y1="106" x2="105" y2="106" stroke="#{a}" stroke-width="1.5" stroke-opacity="0.65"/>'
        # label bottom rule
        f'<line x1="17" y1="213" x2="105" y2="213" stroke="#{a}" stroke-width="1.5" stroke-opacity="0.65"/>'
        # centre brand lines
        f'<line x1="29" y1="145" x2="93" y2="145" stroke="#{a}" stroke-width="1.2" stroke-opacity="0.90"/>'
        f'<line x1="35" y1="160" x2="87" y2="160" stroke="#{a}" stroke-width="0.8" stroke-opacity="0.70"/>'
        f'<line x1="31" y1="174" x2="91" y2="174" stroke="#{a}" stroke-width="0.8" stroke-opacity="0.60"/>'
        f'<line x1="37" y1="187" x2="85" y2="187" stroke="#{a}" stroke-width="0.7" stroke-opacity="0.50"/>'
        # neck taper
        f'<path d="M17,56 Q17,46 61,46 Q105,46 105,56 L105,68 L17,68 Z"'
        f' fill="#{a}50" stroke="#{a}99" stroke-width="1"/>'
        # top lid dome
        f'<ellipse cx="61" cy="52" rx="36" ry="7" fill="#{a}65" stroke="#{a}" stroke-width="1"/>'
        # ring pull tab
        f'<ellipse cx="61" cy="44" rx="9" ry="5" fill="none" stroke="#{a}" stroke-width="1.8"/>'
        f'<line x1="61" y1="39" x2="61" y2="34" stroke="#{a}" stroke-width="2" stroke-linecap="round"/>'
        f'<ellipse cx="61" cy="31" rx="6" ry="3.5" fill="none" stroke="#{a}" stroke-width="1.4"/>'
        f'</svg>'
    )


def generate_product_visual(category: str, accent_hex: str, tone: str) -> str:
    """
    Returns a positioned <div> containing the hero product SVG illustration.
    Designed to be inserted inside .ig between the abstract background SVG and
    the vignette divs — so the cinematic vignette fade applies naturally over
    the product base, creating a studio-shot emergence effect.

    z-index:2 places it above the bg SVG (z-index:1) but below vignettes (z-index:4,5).
    """
    _renders = {
        "skincare":   _product_skincare,
        "fitness":    _product_fitness,
        "technology": _product_technology,
        "fashion":    _product_fashion,
        "beverage":   _product_beverage,
    }
    render_fn = _renders.get(category)
    if not render_fn:
        return ""

    accent = accent_hex.lstrip("#")
    svg    = render_fn(accent)

    # Compute rgba glow for drop-shadow filter
    try:
        r = int(accent[:2], 16)
        g = int(accent[2:4], 16)
        b = int(accent[4:6], 16)
        glow = f"drop-shadow(0 0 55px rgba({r},{g},{b},0.42))"
    except Exception:
        glow = "none"

    # Bold/asymmetric tones shift product right to balance left-aligned headline
    h_pos = "55%" if tone == "bold" else "50%"

    return (
        f'<div style="position:absolute;bottom:14px;left:{h_pos};'
        f'transform:translateX(-50%);z-index:2;pointer-events:none;'
        f'filter:{glow};">'
        f'{svg}'
        f'</div>'
    )
