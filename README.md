# Portuguese Tourism RAG Data Pipeline

A beginner-friendl pipeline for collecting data to feed a RAG (Retrieval-Augmented Generation) system about Portuguese Tourism.

> **📖 See [GUIDELINES.md](GUIDELINES.md) for development rules** (simple code, verbose logging, heavy comments)

## Pipeline Overview

```
DATA COLLECTION:
  Step 0: 00__rss_feeds.py    → Configuration (list of RSS feeds)
             ↓
  Step 1: 01__indexer.py      → Collects article links from RSS feeds
             ↓                   Output: data/links/<SOURCE>/*.jsonl
  Step 2: 02__scraper.py      → Scrapes full article content (ScrapingBee)
             ↓                   Output: data/articles/*.json
  Step 3: 03__wiki_fetcher.py → Fetches Wikipedia articles
                                 Output: data/wiki/*.json

RAG SYSTEM:
  Step 10: 10__embedder.py    → Creates embeddings for all documents
             ↓                   Output: data/vectordb/
  Step 11: 11__web_app.py     → Web interface for asking questions
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
python 01__indexer.py
```

### 3. Run the Scraper (Step 2)

```bash
export SCRAPINGBEE_API_KEY="your_api_key_here"

# Scrape 2 articles from each source (for calibration)
python 02__scraper.py --per-source 2

# Scrape all articles
python 02__scraper.py
```

### 4. Fetch Wikipedia Articles (Step 3)

```bash
python 03__wiki_fetcher.py

# With category crawling for more articles
python 03__wiki_fetcher.py --crawl-categories
```

### 5. Create Embeddings (Step 10)

Processes all collected documents and creates vector embeddings:

```bash
export OPENAI_API_KEY="your_api_key_here"

python 10__embedder.py

# Reset and re-embed everything
python 10__embedder.py --reset
```

### 6. Start Web Interface (Step 11)

```bash
export OPENAI_API_KEY="your_api_key_here"

python 11__web_app.py

# Open in browser: http://localhost:9999
```

### Using Make Commands

```bash
make install      # Set up venv and install dependencies
make index        # Run RSS indexer
make scrape       # Scrape articles (needs SCRAPINGBEE_API_KEY)
make wiki         # Fetch Wikipedia articles
make embed        # Create embeddings (needs OPENAI_API_KEY)
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
