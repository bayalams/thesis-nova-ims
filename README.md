# Portuguese Tourism RAG Data Pipeline

A beginner-friendly pipeline for collecting data to feed a RAG (Retrieval-Augmented Generation) system about Portuguese Tourism.

> **📖 See [GUIDELINES.md](GUIDELINES.md) for development rules** (simple code, verbose logging, heavy comments)

## Pipeline Overview

```
DATA COLLECTION:
  Step 0: 00__rss_feeds.py    → Configuration (list of RSS feeds)
             ↓
  Step 1: src/01__indexer.py      → Collects article links from RSS feeds
             ↓                   Output: data/links/<SOURCE>/*.jsonl
  Step 2: src/02__scraper.py      → Scrapes full article content (ScrapingBee)
             ↓                   Output: data/articles/*.json
  Step 3: src/04__wiki_fetcher.py → Fetches Wikipedia articles
                                 Output: data/wiki/*.json

RAG SYSTEM:
  Step 10: src/10__embedder.py    → Creates embeddings for all documents
             ↓                   Output: data/vectordb/
  Step 11: src/11__web_app.py     → Web interface for asking questions
                                 URL: http://localhost:9999
```

## Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Indexer (Step 1)

Collects article links with ALL metadata (author, tags, media, etc.):

```bash
python src/01__indexer.py
```

### 3. Run the Scraper (Step 2)

```bash
export SCRAPINGBEE_API_KEY="your_api_key_here"

# Scrape 2 articles from each source (for calibration)
python src/02__scraper.py --per-source 2

# Scrape all articles
python src/02__scraper.py
```

### 4. Fetch Wikipedia Articles (Step 3)

```bash
python src/04__wiki_fetcher.py

# With category crawling for more articles
python src/04__wiki_fetcher.py --crawl-categories
```

### 5. Create Embeddings (Step 10)

Processes all collected documents and creates vector embeddings:

```bash
# Embedder currently uses Azure OpenAI credentials
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_azure_key"
export AZURE_EMBEDDING_DEPLOYMENT="text-embedding-3-large"

python src/10__embedder.py

# Reset and re-embed everything
python src/10__embedder.py --reset
```

### 6. Start Web Interface (Step 11)

```bash
# OpenAI API (recommended/stable path)
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_LLM_MODEL="gpt-4o-mini"
export OPENAI_EMBEDDING_MODEL="text-embedding-3-large"

# Provider selection (optional):
# export LLM_PROVIDER="auto"   # default
# export LLM_PROVIDER="openai"

python src/11__web_app.py

# Open in browser: http://localhost:9999
```

Web app command-line options:

```bash
python src/11__web_app.py --provider auto
python src/11__web_app.py --provider openai
python src/11__web_app.py --use-wikipedia
python src/11__web_app.py --no-wikipedia
```

### Using Make Commands

```bash
make install      # Set up venv and install dependencies
make index        # Run RSS indexer
make scrape       # Scrape articles (needs SCRAPINGBEE_API_KEY)
make wiki         # Fetch Wikipedia articles
make embed        # Create embeddings (credentials validated by embedder script)
make web          # Start web interface
make rag          # Run embed + web together
make clean        # Remove all data
```

## Data Sources

### RSS Feeds (16 sources)
- **Portuguese**: Público, Expresso, Correio da Manhã, The Portugal News
- **Spanish**: ABC España
- **European**: Euronews (Travel, News, Culture), Le Figaro Voyages, ANSA Viaggi
- **International**: NYT (Travel, World), Condé Nast Traveler, Travel+Leisure, Skift, Al Jazeera

### Wikipedia (70+ articles)
- Tourism destinations, heritage sites, economy, culture
- European tourism trends, sustainable tourism, digital nomadism

## Troubleshooting

- Empty answers:
  - The web app now shows an explicit error banner instead of silently blank output.
  - Check server logs for request ID, model response metadata, and refusal details.
- Unsupported model parameters (`max_tokens`, `temperature`):
  - The app auto-retries with compatible params and logs the final parameter set used.
- Embedding dimension mismatch:
  - Startup sanity check compares live embedding dimension with ChromaDB dimension.
  - Re-embed documents if dimensions differ.
- Provider misconfiguration:
  - Startup logs include provider, endpoint host, model names, and API key prefix (masked).
  - For the web app, use `OPENAI_API_KEY` (+ optional model overrides).
