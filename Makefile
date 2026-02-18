# =============================================================================
# Makefile for Portuguese Tourism RAG Pipeline
# =============================================================================

SHELL := /bin/bash

# Python / venv settings
PYTHON_BIN ?= python3.12
VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PROVIDER ?= openai

.DEFAULT_GOAL := help

# =============================================================================
# HELP
# =============================================================================

help:
	@echo "============================================================"
	@echo "Portuguese Tourism RAG Pipeline"
	@echo "============================================================"
	@echo ""
	@echo "Usage: make <target>"
	@echo "       make web PROVIDER=openai|azure"
	@echo ""
	@echo "Setup:"
	@echo "  install       - Create venv and install dependencies"
	@echo ""
	@echo "Data Collection:"
	@echo "  index         - Step 1: Collect RSS feed links"
	@echo "  scrape        - Step 2: Scrape article content (needs SCRAPINGBEE_API_KEY)"
	@echo "  scrape-sample - Step 2: Scrape 2 articles per source"
	@echo "  scrape-retry  - Step 2: Re-scrape only previously failed articles"
	@echo "  wiki          - Step 3: Fetch Wikipedia articles"
	@echo "  wiki-full     - Step 3: Fetch Wikipedia + categories"
	@echo ""
	@echo "RAG System:"
	@echo "  embed         - Step 10: Create embeddings"
	@echo "  web           - Step 11: Start web app (choose with PROVIDER=openai|azure)"
	@echo "  web-wiki      - Step 11: Start web app + Wikipedia (PROVIDER=openai|azure)"
	@echo "  rag           - Run embed + web"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean         - Remove collected data + vectordb"
	@echo "  clean-all     - Remove data + venv"
	@echo ""

# =============================================================================
# SETUP
# =============================================================================

install:
	@echo "[SETUP] Creating virtual environment with $(PYTHON_BIN)..."
	@if ! command -v $(PYTHON_BIN) >/dev/null 2>&1; then \
		echo "[ERROR] $(PYTHON_BIN) not found."; \
		echo "Install Python 3.12 or run: make install PYTHON_BIN=python3.11"; \
		exit 1; \
	fi
	$(PYTHON_BIN) -m venv $(VENV)
	@echo "[SETUP] Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "[DONE] Setup complete"

# =============================================================================
# PIPELINE STEPS
# =============================================================================

index:
	@echo "============================================================"
	@echo "Step 1: RSS Feed Indexer"
	@echo "============================================================"
	$(PYTHON) src/01__indexer.py

scrape:
	@echo "============================================================"
	@echo "Step 2: Article Scraper"
	@echo "============================================================"
	@if [ -z "$$SCRAPINGBEE_API_KEY" ]; then \
		echo "[ERROR] SCRAPINGBEE_API_KEY not set"; \
		echo "Run: export SCRAPINGBEE_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) src/02__scraper.py

scrape-sample:
	@echo "============================================================"
	@echo "Step 2: Article Scraper (2 per source)"
	@echo "============================================================"
	@if [ -z "$$SCRAPINGBEE_API_KEY" ]; then \
		echo "[ERROR] SCRAPINGBEE_API_KEY not set"; \
		echo "Run: export SCRAPINGBEE_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) src/02__scraper.py --per-source 2

scrape-retry:
	@echo "============================================================"
	@echo "Step 2: Re-scraping Failed Articles"
	@echo "============================================================"
	@if [ -z "$$SCRAPINGBEE_API_KEY" ]; then \
		echo "[ERROR] SCRAPINGBEE_API_KEY not set"; \
		echo "Run: export SCRAPINGBEE_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) src/02__scraper.py --retry-failed

wiki:
	@echo "============================================================"
	@echo "Step 3: Wikipedia Fetcher"
	@echo "============================================================"
	$(PYTHON) src/04__wiki_fetcher.py

wiki-full:
	@echo "============================================================"
	@echo "Step 3: Wikipedia Fetcher (with categories)"
	@echo "============================================================"
	$(PYTHON) src/04__wiki_fetcher.py --crawl-categories

# =============================================================================
# SHORTCUTS
# =============================================================================

all: index scrape wiki
	@echo "[DONE] Data collection steps completed"

update: index wiki
	@echo "[DONE] Update completed (index + wiki)"

# =============================================================================
# RAG SYSTEM
# =============================================================================

embed:
	@echo "============================================================"
	@echo "Step 10: Document Embedder"
	@echo "============================================================"
	@echo "[INFO] Credential checks run inside src/10__embedder.py"
	$(PYTHON) src/10__embedder.py

# --- Test Configurations for Thesis Evaluation ---
# Each target creates a separate vector database for comparison

embed-test-nochunk:
	@echo "============================================================"
	@echo "Test: No Chunking (full articles)"
	@echo "============================================================"
	$(PYTHON) src/10__embedder.py --provider $(PROVIDER) --no-chunk --db-dir data/vectordb_nochunk --reset

embed-test-small:
	@echo "============================================================"
	@echo "Test: Small Chunks (500 chars / 100 overlap)"
	@echo "============================================================"
	$(PYTHON) src/10__embedder.py --provider $(PROVIDER) --chunk-size 500 --chunk-overlap 100 --db-dir data/vectordb_small_chunks --reset

embed-test-recursive:
	@echo "============================================================"
	@echo "Test: Recursive Chunking (2000 chars / 200 overlap)"
	@echo "============================================================"
	$(PYTHON) src/10__embedder.py --provider $(PROVIDER) --chunk-strategy recursive --db-dir data/vectordb_recursive --reset

embed-test-small-model:
	@echo "============================================================"
	@echo "Test: text-embedding-3-small (1536 dims)"
	@echo "============================================================"
	$(PYTHON) src/10__embedder.py --provider $(PROVIDER) --embedding-model text-embedding-3-small --db-dir data/vectordb_small_model --reset

embed-test-reduced-dims:
	@echo "============================================================"
	@echo "Test: text-embedding-3-large at 1536 dims"
	@echo "============================================================"
	$(PYTHON) src/10__embedder.py --provider $(PROVIDER) --embedding-dims 1536 --db-dir data/vectordb_large_reduced --reset

web:
	@echo "============================================================"
	@echo "Step 11: Web Interface (provider: $(PROVIDER))"
	@echo "============================================================"
	@echo "[INFO] Credential checks run inside src/11__web_app.py"
	$(PYTHON) src/11__web_app.py --provider $(PROVIDER)

web-wiki:
	@echo "============================================================"
	@echo "Step 11: Web Interface + Wikipedia (provider: $(PROVIDER))"
	@echo "============================================================"
	@echo "[INFO] Credential checks run inside src/11__web_app.py"
	$(PYTHON) src/11__web_app.py --provider $(PROVIDER) --use-wikipedia

rag: embed web

# =============================================================================
# MAINTENANCE
# =============================================================================

clean:
	@echo "[CLEAN] Removing data directories..."
	rm -rf data/links data/articles data/wiki data/vectordb
	@echo "[DONE] Data cleaned"

clean-all: clean
	@echo "[CLEAN] Removing virtual environment..."
	rm -rf $(VENV)
	@echo "[DONE] Full cleanup complete"

# =============================================================================
# PHONY TARGETS
# =============================================================================

.PHONY: help install index scrape scrape-sample scrape-retry wiki wiki-full all update embed embed-test-nochunk embed-test-small embed-test-recursive embed-test-small-model embed-test-reduced-dims web web-wiki rag clean clean-all
