# =============================================================================
# Makefile for Portuguese Tourism RAG Pipeline
# =============================================================================
#
# Usage:
#   make install     - Install dependencies
#   make index       - Run RSS indexer (Step 1)
#   make scrape      - Run article scraper (Step 2) - requires SCRAPINGBEE_API_KEY
#   make wiki        - Fetch Wikipedia articles (Step 3)
#   make all         - Run all steps
#   make update      - Run index + wiki (no scraping)
#   make clean       - Remove all data
#
# =============================================================================

# Python executable (use venv)
PYTHON = .venv/bin/python

# Default target
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
	@echo ""
	@echo "Setup:"
	@echo "  install     - Create venv and install dependencies"
	@echo ""
	@echo "Data Collection:"
	@echo "  index       - Step 1: Collect RSS feed links"
	@echo "  scrape      - Step 2: Scrape article content (needs API key)"
	@echo "  wiki        - Step 3: Fetch Wikipedia articles"
	@echo ""
	@echo "RAG System:"
	@echo "  embed       - Step 10: Create embeddings for all documents"
	@echo "  web         - Step 11: Start the web interface"
	@echo ""
	@echo "Shortcuts:"
	@echo "  all         - Run all data collection steps"
	@echo "  update      - Run index + wiki (skip scraping)"
	@echo "  rag         - Run embed + web (start RAG system)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       - Remove all collected data"
	@echo "  clean-all   - Remove data AND venv"
	@echo ""

# =============================================================================
# SETUP
# =============================================================================

install:
	@echo "[SETUP] Creating virtual environment..."
	python3 -m venv .venv
	@echo "[SETUP] Installing dependencies..."
	.venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "[DONE] Setup complete! Run 'make index' to start."

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
		echo "[ERROR] SCRAPINGBEE_API_KEY not set!"; \
		echo ""; \
		echo "Run: export SCRAPINGBEE_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) src/02__scraper.py

scrape-sample:
	@echo "============================================================"
	@echo "Step 2: Article Scraper (2 per source)"
	@echo "============================================================"
	@if [ -z "$$SCRAPINGBEE_API_KEY" ]; then \
		echo "[ERROR] SCRAPINGBEE_API_KEY not set!"; \
		echo ""; \
		echo "Run: export SCRAPINGBEE_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) src/02__scraper.py --per-source 2

wiki:
	@echo "============================================================"
	@echo "Step 3: Wikipedia Fetcher"
	@echo "============================================================"
	$(PYTHON) src/03__wiki_fetcher.py

wiki-full:
	@echo "============================================================"
	@echo "Step 3: Wikipedia Fetcher (with categories)"
	@echo "============================================================"
	$(PYTHON) src/03__wiki_fetcher.py --crawl-categories

# =============================================================================
# SHORTCUTS
# =============================================================================

all: index scrape wiki
	@echo ""
	@echo "============================================================"
	@echo "All steps completed!"
	@echo "============================================================"

update: index wiki
	@echo ""
	@echo "============================================================"
	@echo "Update completed (index + wiki)!"
	@echo "============================================================"

# =============================================================================
# RAG SYSTEM
# =============================================================================

embed:
	@echo "============================================================"
	@echo "Step 10: Document Embedder"
	@echo "============================================================"
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "[ERROR] OPENAI_API_KEY not set!"; \
		echo ""; \
		echo "Run: export OPENAI_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) 10__embedder.py

web:
	@echo "============================================================"
	@echo "Step 11: Web Interface"
	@echo "============================================================"
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "[ERROR] OPENAI_API_KEY not set!"; \
		echo ""; \
		echo "Run: export OPENAI_API_KEY='your_key'"; \
		exit 1; \
	fi
	$(PYTHON) 11__web_app.py

rag: embed web

# =============================================================================
# MAINTENANCE
# =============================================================================

clean:
	@echo "[CLEAN] Removing data directories..."
	rm -rf data/links data/articles data/wiki data/vectordb
	@echo "[DONE] Data cleaned."

clean-all: clean
	@echo "[CLEAN] Removing virtual environment..."
	rm -rf .venv
	@echo "[DONE] Full cleanup complete."

# =============================================================================
# PHONY TARGETS
# =============================================================================

.PHONY: help install index scrape scrape-sample wiki wiki-full all update embed web rag clean clean-all
