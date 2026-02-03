# 🏗️ News RAG Pipeline Architecture

This document outlines the end-to-end flow for processing news articles from diverse sources (Público, Expresso, ABC, etc.) into a high-quality knowledge base for Retrieval Augmented Generation (RAG).

---

## 1. Data Ingestion (Scraping)
**Goal:** Acquire raw HTML/JSON content from diverse news sites.
*   **Input:** URL Lists.
*   **Tool:** ScrapingBee (handles JS rendering/proxies).
*   **Filtering (New):**
    *   **Video Filter:** Pre-check URLs for `/video/` signals to skip irrelevant multimedia pages.
*   **Output:** Raw JSON files containing `metadata` (author, date) and `scrapingbee.content` (raw HTML/Text).

---

## 2. Pre-processing (Cleaning & Enrichment) 
**Goal:** Transform "noisy" raw text into "clean" semantic content. **(Current Focus)**
*   **Input:** Raw JSON files.
*   **Logic:** `clean_and_enrich_text(text, meta)`
    1.  **Defense Check:** Re-verify if it's a video page (returns empty if yes).
    2.  **Source Dispatcher:** 
        *   Determines source (e.g., `ABC_ESPANA`, `PUBLICO`, `EXPRESSO`).
        *   Routes to specialized cleaning function.
    3.  **Source-Specific Cleaning:**
        *   **Header Trimming (`Title Seeker`):** Finds the article title within the body and cuts everything before it (removes massive navigation menus).
        *   **Footer Trimming:** Cuts text after specific triggers (e.g., "Reportar um erro", "Subscreva").
        *   **Inline Noise Removal:** Regex removal of:
            *   *Ads / Subscription Prompts* ("Esta funcionalidade é só para...").
            *   *Social Media Junk* ("Partilhar no Facebook").
            *   *Widgets* (Lottery checkers, stock tickers).
    4.  **Metadata Injection (Enrichment):**
        *   Prepends standardized header to the clean text. 
        *   **Why?** Ensures the Chunker & Embedder "see" the date and context even if the chunk is in the middle of the text.
        ```text
        DATE: 2026-01-08
        TAGS: Politics, Europe
        TITLE: Title of the news article
        ====================
        [Clean Article Body...]
        ```
*   **Output:** Clean, dense text string with metadata header.

---

## 3. Segmentation (Chunking)
**Goal:** Split long articles into smaller, self-contained semantic units.
*   **Input:** Cleaned Text.
*   **Strategy:** Recursive Character Splitter (Recommended).
    *   **Chunk Size:** ~500-1000 tokens (depending on embedding model limit).
    *   **Overlap:** ~10-15% (preserves context across boundaries).
    *   **Separators:** `\n\n` (Paragraphs) -> `\n` (Lines) -> `.` (Sentences).
*   **Why Clean First?** 
    *   If you chunk *before* cleaning, a 500-token chunk might be entirely "Subscribe Now" links, creating "poisoned" vectors that match irrelevant queries.

---

## 4. Embedding
**Goal:** Convert text chunks into mathematical vectors (lists of numbers).
*   **Input:** Text Chunks.
*   **Model:** OpenAI (`text-embedding-3-small` / `large`) or similar.
*   **Process:** 
    *   Each chunk is sent to the API.
    *   API returns a vector (e.g., float array of length 1536).
*   **Storage:** The vector + the original text chunk are saved together.

---

## 5. Vector Storage (Knowledge Base)
**Goal:** Store vectors for fast similarity search.
*   **Tool:** ChromaDB, Pinecone, or FAISS.
*   **Structure:**
    *   **Collection:** "News_Articles"
    *   **Payload:**
        *   `id`: Unique Chunk ID.
        *   `vector`: [0.12, -0.98, ...]
        *   `metadata`: { "source": "ABC", "date": "2026-01-08", "url": "..." }
        *   `text`: "The actual content of the chunk..."

---

## 6. Retrieval & Generation (RAG)
**Goal:** Answer user questions using the knowledge base.
1.  **User Query:** "What happened in the ABC lottery news?"
2.  **Query Embedding:** Convert question to vector.
3.  **Search:** Find top K chunks closest to the query vector.
4.  **Synthesis:** Feed chunks + Question to LLM (GPT-4) to generate answer.
