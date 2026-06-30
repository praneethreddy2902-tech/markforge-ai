
"""
Two-panel layout:
  LEFT  sidebar → source selector (URL or PDF) + controls
  RIGHT main    → poster + brand DNA + content
"""

import streamlit as st
import streamlit.components.v1 as components
import sys, os
sys.path.insert(0, os.path.abspath("."))


st.set_page_config(
    page_title="MarkForge AI",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: #0d0d14 !important;
    color: #f0f0f8 !important;
}
.stApp { background: #0d0d14 !important; }
#MainMenu, footer, header, .stDeployButton { visibility: hidden !important; display: none !important; }
.block-container { padding: 2rem 2.5rem !important; }

/* sidebar */
section[data-testid="stSidebar"] {
    background: #111118 !important;
    border-right: 1px solid #1e1e2e !important;
}
section[data-testid="stSidebar"] .block-container { padding: 2rem 1.5rem !important; }

/* input */
.stTextInput input {
    background: #1a1a28 !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #f0f0f8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 0.65rem 1rem !important;
}
.stTextInput input:focus { border-color: #e94560 !important; box-shadow: 0 0 0 2px rgba(233,69,96,0.15) !important; }

/* generate button */
.stButton > button {
    background: linear-gradient(135deg, #e94560, #c73652) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem !important;
    width: 100% !important;
    letter-spacing: 0.5px !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; transform: none !important; }

/* section header */
.sec {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #e94560;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin: 1.5rem 0 0.6rem;
}

/* tagline / headline cards */
.tcard {
    background: #1a1a28;
    border: 1px solid #2a2a3e;
    border-left: 3px solid #e94560;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #f0f0f8;
}
.hcard {
    background: #1a1a28;
    border: 1px solid #2a2a3e;
    border-left: 3px solid #ffd166;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: 0.02em;
}

/* marketing copy box */
.mcopy {
    background: rgba(233,69,96,0.06);
    border: 1px solid rgba(233,69,96,0.2);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.92rem;
    line-height: 1.75;
    color: #e0e0f0;
    font-style: italic;
}

/* social post box */
.spost {
    background: rgba(67,97,238,0.08);
    border: 1px solid rgba(67,97,238,0.25);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.9rem;
    line-height: 1.7;
    color: #d0d0e8;
}

/* CTA display */
.cta-display {
    display: inline-block;
    background: #e94560;
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 0.9rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 10px 24px;
    border-radius: 6px;
    margin-top: 0.4rem;
}

/* Brand DNA grid */
.dna-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 0.5rem;
}
.dna-card {
    background: #1a1a28;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
    padding: 0.65rem 0.9rem;
}
.dna-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: #e94560;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 4px;
}
.dna-value {
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    color: #e0e0f0;
    line-height: 1.3;
}

/* feature row */
.feat {
    display: flex;
    gap: 10px;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1e1e2e;
    font-size: 0.875rem;
    color: #a0a0c0;
}
.feat:last-child { border-bottom: none; }
.feat-dot { color: #06d6a0; flex-shrink: 0; }

/* poster wrap */
.poster-wrap {
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

/* status pills */
.pill-ok  { display:inline-block; background:rgba(6,214,160,0.12); color:#06d6a0; border:1px solid rgba(6,214,160,0.3); border-radius:20px; padding:3px 12px; font-family:'JetBrains Mono',monospace; font-size:0.7rem; }
.pill-err { display:inline-block; background:rgba(233,69,96,0.12); color:#e94560; border:1px solid rgba(233,69,96,0.3); border-radius:20px; padding:3px 12px; font-family:'JetBrains Mono',monospace; font-size:0.7rem; }
.pill-run { display:inline-block; background:rgba(255,209,102,0.12); color:#ffd166; border:1px solid rgba(255,209,102,0.3); border-radius:20px; padding:3px 12px; font-family:'JetBrains Mono',monospace; font-size:0.7rem; }

/* PDF source badge */
.pdf-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(67,97,238,0.1);
    border: 1px solid rgba(67,97,238,0.3);
    border-radius: 8px;
    padding: 6px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #7b97ff;
    margin-bottom: 0.75rem;
    max-width: 100%;
    word-break: break-all;
}

/* file uploader dark theme */
[data-testid="stFileUploader"] {
    background: #1a1a28 !important;
    border: 1px dashed #2a2a3e !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"] label {
    color: #a0a0c0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}
[data-testid="stFileUploadDropzone"] {
    background: #1a1a28 !important;
    border: 1px dashed #2a2a3e !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: #e94560 !important;
}

/* mode radio */
.stRadio [role="radiogroup"] {
    gap: 6px !important;
}
.stRadio [role="radiogroup"] label {
    background: #1a1a28 !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    color: #a0a0c0 !important;
    cursor: pointer !important;
    transition: border-color 0.15s !important;
}
.stRadio [role="radiogroup"] label:hover {
    border-color: #e94560 !important;
    color: #f0f0f8 !important;
}

hr { border-color: #1e1e2e !important; }
.stDownloadButton > button { background: #1a1a28 !important; border: 1px solid #2a2a3e !important; color: #a0a0c0 !important; font-size: 0.8rem !important; }
.stDownloadButton > button:hover { border-color: #e94560 !important; color: #e94560 !important; }
</style>
""", unsafe_allow_html=True)


from src.rag_pipeline import run_pipeline
from src.pdf_pipeline import run_pdf_pipeline
from src.retrieval.retriever import retrieve_and_format
from src.llm_service.claude_api import get_claude_response
from src.llm_service.prompt_templates import get_chat_prompt
import config


for k, v in [("result", None), ("url", None), ("chat", []), ("source_key", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


generate      = False
generate_pdf  = False
force_refresh = False
url_input     = ""
uploaded_pdf  = None

with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:1.5rem;">
        <div style="font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800; color:#f0f0f8;">
            🔥 MarkForge AI
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#555570; margin-top:4px;">
            RAG · BRAND INTELLIGENCE · MARKETING
        </div>
    </div>
    """, unsafe_allow_html=True)

    
    st.markdown('<div class="sec">Input Source</div>', unsafe_allow_html=True)
    input_mode = st.radio(
        "input_mode",
        ["🌐 Website", "📄 PDF"],
        horizontal=True,
        label_visibility="collapsed",
    )

    
    if input_mode == "🌐 Website":
        st.markdown('<div class="sec">Website URL</div>', unsafe_allow_html=True)
        
        url_input = st.text_input(
            "url",
            key="url_value",
            placeholder="https://www.nike.com",
            label_visibility="collapsed"
        )

        force_refresh = st.toggle("🔄 Force fresh scrape", value=False)
        generate = st.button("⚡  Generate Content", use_container_width=True)

        st.markdown("---")
        st.markdown('<div class="sec">Major Brands</div>', unsafe_allow_html=True)
        st.caption("Auto-fallback to Wikipedia if site blocks scrapers.")

        brand_urls = {
            "Nike":       "https://www.nike.com",
            "Apple":      "https://www.apple.com",
            "Adidas":     "https://www.adidas.com",
            "Red Bull":   "https://www.redbull.com",
            "Puma":       "https://www.puma.com",
            "Coca-Cola":  "https://www.coca-cola.com",
            "Spotify":    "https://www.spotify.com",
            "Dior":       "https://www.dior.com",
            "Tesla":      "https://www.tesla.com",
            "Samsung":    "https://www.samsung.com",
        }

        cols = st.columns(2)
        for i, (name, qurl) in enumerate(brand_urls.items()):
            if cols[i % 2].button(name, key=f"q_{name}", use_container_width=True):
                st.session_state["url_value"]      = qurl
                st.session_state["_auto_generate"] = True
                st.rerun()

        st.markdown("---")
        st.markdown('<div class="sec">Other URLs</div>', unsafe_allow_html=True)
        other_urls = {
            "Anthropic":  "https://www.anthropic.com",
            "Streamlit":  "https://streamlit.io",
            "Figma":      "https://www.figma.com",
        }
        for name, qurl in other_urls.items():
            if st.button(name, key=f"q_{name}"):
                st.session_state["url_value"]      = qurl
                st.session_state["_auto_generate"] = True
                st.rerun()

    
    else:
        st.markdown('<div class="sec">PDF Document</div>', unsafe_allow_html=True)
        uploaded_pdf = st.file_uploader(
            "Upload brand PDF",
            type=["pdf"],
            label_visibility="collapsed",
            help="Upload a brand document, brand guide, annual report, or product brief.",
        )

        if uploaded_pdf:
            size_kb = uploaded_pdf.size // 1024
            st.markdown(
                f'<div class="pdf-badge">📄 {uploaded_pdf.name} &nbsp;·&nbsp; {size_kb} KB</div>',
                unsafe_allow_html=True
            )

        generate_pdf = st.button("⚡  Generate from PDF", use_container_width=True)

        st.markdown("---")
        st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#444460; line-height:2;">
            <div>✓ &nbsp;Brand guides &amp; style docs</div>
            <div>✓ &nbsp;Annual reports</div>
            <div>✓ &nbsp;Product briefs &amp; pitch decks</div>
            <div>✗ &nbsp;Scanned / image-only PDFs</div>
        </div>
        """, unsafe_allow_html=True)

    
    st.markdown("---")
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#444460; line-height:1.9;">
        <div>Model &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'Ollama' if config.USE_LOCAL_MODEL else 'Claude'}</div>
        <div>Chunks &nbsp;&nbsp;&nbsp;&nbsp;{config.TOP_K_RESULTS} retrieved</div>
        <div>Chunk sz &nbsp;&nbsp;{config.CHUNK_SIZE} chars</div>
        <div>Embedder &nbsp;&nbsp;MiniLM-L6-v2</div>
        <div>VectorDB &nbsp;&nbsp;ChromaDB</div>
    </div>
    """, unsafe_allow_html=True)

    
    if st.session_state.get("result") and st.session_state["result"].get("success"):
        r = st.session_state["result"]
        st.markdown("---")
        st.markdown('<div class="sec">Last Run Metrics</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.metric("Latency", f"{r['latency']}s")
        col2.metric("Similarity", f"{r.get('avg_similarity', 0):.3f}")
        if r.get("from_cache"):
            st.success("⚡ Served from cache")


_auto = st.session_state.pop("_auto_generate", False)
if (generate or _auto) and url_input:
    st.session_state.chat = []
    with st.spinner("Running pipeline..."):
        res = run_pipeline(url_input, force_refresh=force_refresh)
    st.session_state.result     = res
    st.session_state.url        = url_input
    st.session_state.source_key = url_input


if generate_pdf and uploaded_pdf:
    st.session_state.chat = []
    with st.spinner("Extracting text and running RAG pipeline…"):
        pdf_bytes = uploaded_pdf.read()
        res = run_pdf_pipeline(pdf_bytes, uploaded_pdf.name)
    st.session_state.result     = res
    st.session_state.url        = None
    st.session_state.source_key = res.get("source_key") if res.get("success") else None
elif generate_pdf and not uploaded_pdf:
    st.warning("Please upload a PDF file first.")


res = st.session_state.result

if res is None:
    st.markdown("""
    <div style="text-align:center; padding:5rem 2rem; opacity:0.5;">
        <div style="font-family:'Syne',sans-serif; font-size:2rem; font-weight:800; margin-bottom:0.5rem;">
            Enter a URL or upload a PDF
        </div>
        <div style="font-size:0.9rem; color:#666680;">
            MarkForge AI scrapes any website — or reads a PDF — and generates
            brand-specific marketing content and a visual poster.
        </div>
    </div>
    """, unsafe_allow_html=True)

elif not res["success"]:
    st.markdown('<span class="pill-err">✗ FAILED</span>', unsafe_allow_html=True)
    st.error(f"{res['error']}")
    if input_mode == "🌐 Website":
        st.info("Large brand websites (Nike.com, Apple.com) block scrapers. Use the Wikipedia URLs instead.")

else:
    parsed = res.get("parsed_output", {})
    st.markdown(f'<span class="pill-ok">✓ Done in {res["latency"]}s</span>', unsafe_allow_html=True)

    # Source label — URL or PDF filename
    source_key = st.session_state.get("source_key", "")
    if source_key and source_key.startswith("pdf::"):
        pdf_name = source_key.removeprefix("pdf::")
        st.markdown(
            f'<div class="pdf-badge">📄 {pdf_name}</div>',
            unsafe_allow_html=True
        )

    
    fallback_note = res.get("brand_assets", {}).get("_fallback_note", "")
    if fallback_note or res.get("fallback_used"):
        st.info(
            "ℹ️  **Wikipedia fallback used** — the brand's official site blocked our scraper. "
            "Content is sourced from Wikipedia. Brand colors and imagery are applied from the "
            "brand registry for an authentic poster.",
            icon=None,
        )

    
    st.markdown('<div class="sec" style="margin-top:1rem;">Brand Poster</div>', unsafe_allow_html=True)

    poster_html = parsed.get("poster_html", "")
    if poster_html:
        st.markdown('<div class="poster-wrap">', unsafe_allow_html=True)
        components.html(poster_html, height=820, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇️  Download Poster",
            data=poster_html,
            file_name="markforge_poster.html",
            mime="text/html",
            use_container_width=True
        )

        
        credits = res.get("brand_assets", {}).get("unsplash_credits", [])
        if credits:
            credit_parts = [
                f"[{c['name']}]({c['profile']}?utm_source=markforge_ai&utm_medium=referral)"
                for c in credits
            ]
            st.caption(
                "📸 Photos by " + " · ".join(credit_parts) +
                " on [Unsplash](https://unsplash.com/?utm_source=markforge_ai&utm_medium=referral)"
            )
    else:
        st.warning("No poster generated — try regenerating.")

    st.markdown("---")

    
    dna_fields = {
        "Personality":  parsed.get("brand_personality", ""),
        "Audience":     parsed.get("target_audience", ""),
        "Emotion":      parsed.get("emotional_appeal", ""),
        "Visual Style": parsed.get("visual_direction", ""),
        "Voice":        parsed.get("marketing_tone", ""),
        "Color Mood":   parsed.get("color_style", ""),
    }
    if any(dna_fields.values()):
        st.markdown('<div class="sec">Brand DNA</div>', unsafe_allow_html=True)
        dna_html = '<div class="dna-grid">'
        for label, value in dna_fields.items():
            if value:
                dna_html += (
                    f'<div class="dna-card">'
                    f'<div class="dna-label">{label}</div>'
                    f'<div class="dna-value">{value}</div>'
                    f'</div>'
                )
        dna_html += '</div>'
        st.markdown(dna_html, unsafe_allow_html=True)

    st.markdown("---")

    
    with st.expander("🔍 RAG: Retrieved Chunks Used for Generation", expanded=False):
        st.caption(
            f"These {res.get('chunks_used', 5)} chunks were retrieved from ChromaDB "
            f"using cosine similarity and injected into the Claude prompt as context."
        )
        context_display = res.get("retrieved_context", "")
        if context_display:
            for i, chunk in enumerate(context_display.split("\n\n"), 1):
                if chunk.strip():
                    st.markdown(f"**Chunk {i}**")
                    st.info(chunk.strip())
        else:
            col1, col2 = st.columns(2)
            col1.metric(
                label="Cosine Similarity",
                value=f"{res.get('avg_similarity', 0):.3f}",
                help="Higher = more relevant chunks retrieved"
            )
            col2.metric(
                label="Chunks Retrieved",
                value=res.get("chunks_used", 5),
            )

    
    poster_prompt = parsed.get("poster_prompt", "")
    if poster_prompt:
        with st.expander("🎨 AI Poster Prompt", expanded=False):
            st.caption("Use this prompt with Midjourney, DALL·E, or Stable Diffusion.")
            st.code(poster_prompt, language=None)

    st.markdown("---")

    
    left, right = st.columns(2, gap="large")

    with left:
        brand    = parsed.get("brand_name", "—")
        industry = parsed.get("industry", "—")
        st.markdown(f"""
        <div class="sec">Brand</div>
        <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#f0f0f8;">{brand}</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#555570; margin-top:2px;">{industry}</div>
        """, unsafe_allow_html=True)

        headlines = parsed.get("headlines", [])
        if headlines:
            st.markdown('<div class="sec">Headlines</div>', unsafe_allow_html=True)
            for h in headlines:
                st.markdown(f'<div class="hcard">{h}</div>', unsafe_allow_html=True)

        taglines = parsed.get("taglines", [])
        if taglines:
            st.markdown('<div class="sec">Taglines</div>', unsafe_allow_html=True)
            for tag in taglines:
                st.markdown(f'<div class="tcard">{tag}</div>', unsafe_allow_html=True)

        marketing_para = parsed.get("marketing_paragraph", "")
        if marketing_para:
            st.markdown('<div class="sec">Marketing Copy</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="mcopy">{marketing_para}</div>', unsafe_allow_html=True)

    with right:
        post = parsed.get("social_post", "")
        if post:
            st.markdown('<div class="sec">Social Media Post</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="spost">{post}</div>', unsafe_allow_html=True)

        cta = parsed.get("cta_line", "")
        if cta:
            st.markdown('<div class="sec">CTA Line</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cta-display">{cta}</div>', unsafe_allow_html=True)

        features = parsed.get("key_features", [])
        if features:
            st.markdown('<div class="sec">Key Features</div>', unsafe_allow_html=True)
            html_feat = '<div style="background:#1a1a28; border:1px solid #2a2a3e; border-radius:10px; padding:0.5rem 1rem;">'
            for f in features:
                html_feat += f'<div class="feat"><span class="feat-dot">✦</span>{f}</div>'
            html_feat += '</div>'
            st.markdown(html_feat, unsafe_allow_html=True)

    st.markdown("---")

    
    st.markdown('<div class="sec">Ask About This Brand</div>', unsafe_allow_html=True)
    st.caption("Answers are grounded in the scraped / uploaded content only.")

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    q = st.chat_input("e.g. What are their main products?")
    if q:
        
        chat_source = st.session_state.get("source_key") or st.session_state.get("url")
        if not chat_source:
            st.warning("Please run the pipeline first before using chat.")
            st.stop()

        brand_name_for_chat = st.session_state.result["brand_assets"].get("brand_name", "")
        tone_for_chat       = st.session_state.result["brand_assets"].get("tone", "professional")

        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                try:
                    ctx = retrieve_and_format(
                        query=q,
                        top_k=config.TOP_K_RESULTS,
                        url=chat_source,
                        brand_name=brand_name_for_chat,
                        tone=tone_for_chat,
                    )
                    
                    prompt = get_chat_prompt(ctx, q, chat_source)
                    ans    = get_claude_response(prompt, system_prompt="Answer concisely from context only.")
                    st.write(ans)
                    st.session_state.chat.append({"role": "assistant", "content": ans})
                except Exception as e:
                    st.error(str(e))
