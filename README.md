MarkForge AI

An AI-powered marketing content generator that turns any PDF or website URL into ready-to-use marketing copy — using a Retrieval-Augmented Generation (RAG) pipeline.

🔗 Live Demo: [Add your Streamlit link here]
📂 Source Code: You're here



What It Does

Marketers spend hours manually rewriting the same brand messaging for different platforms. MarkForge AI automates this — give it a product PDF or a landing page URL, and it extracts the core brand context, then generates marketing content grounded in that source material.

Input: PDF document or website URL
Output: AI-generated marketing copy, grounded in the actual source content (not hallucinated)



How It Works

Input (PDF / URL)
        ↓
Document Parsing & Text Extraction
        ↓
Chunking (split into smaller text segments)
        ↓
Embedding (convert chunks into vectors)
        ↓
Vector Storage (ChromaDB)
        ↓
Retrieval (find most relevant chunks for the query)
        ↓
Generation (LLM produces marketing copy from retrieved context)
        ↓
Output: Marketing Content

The core idea behind RAG: instead of relying purely on what the LLM already knows, the pipeline retrieves real, relevant content from the source document first, then asks the model to generate output grounded in that retrieved context. This reduces hallucination and keeps output factually tied to the actual brand material.



Tech Stack







Component



Technology





LLM



OpenAI GPT-4o / GPT-4o-mini





Orchestration



LangChain





Vector Database



ChromaDB





PDF Parsing



PyMuPDF





URL Scraping



BeautifulSoup





Frontend / Demo



Streamlit





Language



Python



Why These Choices





ChromaDB over Pinecone — runs locally with no API costs during development, ideal for an iterating solo project.



Chunking with overlap — prevents context from being cut off mid-sentence at chunk boundaries, improving retrieval relevance.



GPT-4o-mini for generation — strong output quality at a fraction of GPT-4o's cost, making iteration affordable during development.



Setup & Installation

# Clone the repository
git clone https://github.com/praneethreddy2902-tech/markforge-ai.git
cd markforge-ai

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI API key
cp .env.example .env
# then edit .env and add your key:
# OPENAI_API_KEY=your-key-here

# Run the app
streamlit run app.py



Roadmap

This project is under active development. Planned upgrades:





Tone selector — generate content for specific channels (LinkedIn, Twitter, cold email, ad copy)



Structured JSON output via LangChain output parsers



FastAPI backend — expose generation as a REST API



LLM-as-judge evaluation — automated quality scoring for generated copy



MCP server integration — expose MarkForge as a callable tool for LLM agents



Project Background

Originally built as a B.Tech capstone project under the Information Technology department at Manipal University Jaipur, MarkForge AI has since evolved with a dual-input architecture (PDF + URL) and is being actively upgraded toward a production-style deployment with structured outputs and automated evaluation.



Author

Praneeth Reddy
B.Tech Information Technology, Manipal University Jaipur
[LinkedIn] · [Email]
