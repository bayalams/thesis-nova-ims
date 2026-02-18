# Methodology

## 3.1 Overview and Research Design

This chapter describes the end-to-end design, implementation, and evaluation strategy of the Tourism Intelligence Pipeline — a system that continuously ingests multilingual news from Portugal's key tourism source markets, structures it into a tourism-aware Knowledge Base (KB), and delivers source-grounded answers via a Retrieval-Augmented Generation (RAG) architecture. The methodology follows a Design Science Research (DSR) approach (Hevner et al., 2004; Peffers et al., 2007), in which the primary contribution is NOT a statistical hypothesis test but rather a purposefully designed and iteratively refined artifact — the pipeline itself — evaluated against explicit quality criteria (accuracy, traceability, latency, and actionability).

The research design unfolds across three interlinked phases, each mapped to a research question:

| Phase | Research Question | Objective | Key Activities |
|-------|------------------|-----------|----------------|
| **Phase 1 — Data Foundations** | RQ1: Can continuous news/regulatory streams be transformed into actionable market intelligence? | Build a reproducible ingestion, cleaning, and structuring pipeline | Source selection, RSS/API collection, scraping, source-specific cleaning, metadata enrichment, provenance tracking |
| **Phase 2 — Intelligence Layer** | RQ2: Can an automated system classify news into actionable categories? | Implement and evaluate automated news classification | Taxonomy design, classifier training/evaluation, sentiment tagging, alert logic |
| **Phase 3 — KB + RAG Evaluation** | RQ3: Which KB structures and RAG strategies most improve accuracy, traceability, and latency? | Systematically compare chunking, embedding, and retrieval configurations | Controlled ablation study across 6 configurations, human evaluation with standardized queries |

<!--
TODO: INSERT FIGURE 3.1 — Research Design Diagram
A visual flowchart showing the three-phase research design.
Left side: Source Markets (UK, US, DE, FR, ES, PT) → RSS/API feeds
Center: Pipeline stages (Index → Scrape → Clean → Chunk → Embed → Vector KB)
Right side: RAG + Dashboard output
Each phase (1, 2, 3) bracketed around its corresponding pipeline stages.
Arrows showing feedback loops (e.g., evaluation results feeding back into Phase 1 cleaning improvements).
-->

> **Figure 3.1** (to be inserted): Research Design Framework — Three-phase pipeline from multilingual news streams to source-grounded tourism intelligence, mapped to the three research questions.

The remaining sections of this chapter describe each pipeline stage in detail, justify every design decision, relate the approach to prior work, and document the evaluation protocol.

---

## 3.2 Data Collection

### 3.2.1 Source Selection and Justification

Portugal's tourism demand depends heavily on a small number of source markets. According to INE/Turismo de Portugal statistics, the United Kingdom, Spain, Germany, France, and the United States together account for a majority of overnight stays by foreign visitors. To build a system capable of providing actionable, market-specific intelligence (RQ1), the corpus must include media from these origin countries in their native languages, alongside Portuguese domestic media and international trade publications.

The final source portfolio comprises **57 active RSS feeds** spanning **seven languages** (Portuguese, English, Spanish, German, French, Italian, and Dutch) and organized into the following categories:

| Category | Representative Sources | Count | Rationale |
|----------|----------------------|-------|-----------|
| **Portuguese — General & Economy** | Público, Observador, Expresso, RTP Notícias, Diário de Notícias, SAPO, Portugal News, Portugal Resident, ECO/SAPO, Jornal de Negócios, Jornal Económico | 14 | Domestic narrative, policy announcements, visitor statistics |
| **Portuguese — Tourism Trade** | Ambitur | 1 | Industry-insider perspective, trade fairs (BTL, FITUR) |
| **Spain** | El País (General, Economy, Viajero), El Mundo, ABC España, Hosteltur | 6 | Largest land-border market; competitor intelligence |
| **United Kingdom** | BBC Travel, Guardian Travel, Independent Travel, HuffPost Travel | 4 | Top-5 source market; shapes Anglophone perception |
| **Germany** | FAZ, Spiegel Reise, Süddeutsche Reise, Die Zeit | 4 | Top-5 source market; high-spending segment |
| **France** | Le Monde, Le Figaro Voyages, TourMaG, L'Écho Touristique | 4 | Top-5 source market; francophone trade intelligence |
| **Italy** | ANSA Viaggi | 1 | Growing origin market |
| **International — Travel Trade** | Skift, Condé Nast Traveler, Travel + Leisure, CNBC Travel, CNN Travel, Simple Flying, eTurboNews, Breaking Travel News | 8 | Global trends, competitive positioning, aviation signals |
| **International — General** | Al Jazeera, Euronews (News + Travel), France24, DW News, Washington Post, AP News, HuffPost World News | 7-8 | Macro-political events, crisis signals, regulation changes |

All sources are accessed via publicly available RSS feeds (Really Simple Syndication), a lightweight and non-intrusive protocol that respects the publishers' intended syndication model. No paywalled or restricted content is deliberately scraped; sources with hard paywalls (e.g., Wall Street Journal, 0% content retrieval success) or metered paywalls with low success rates (e.g., New York Times Travel, 35% success rate) were empirically tested and subsequently removed from the active feed list to avoid wasting API credits and polluting the knowledge base with incomplete articles (see Section 3.2.4 for details).

### 3.2.2 Indexing Stage

The indexing stage polls all configured RSS feeds, parses entries using the `feedparser` library (Python), and extracts structured metadata for each article: title, publication date, author, tags/categories, media attachments, and the article URL (link). Each article receives a deterministic fingerprint — a SHA-256 hash of the concatenation of title, link, and publication date — to enable deduplication across runs.

A **freshness filter** is applied at indexing time: entries older than a configurable threshold (default: 90 days) are discarded. This addresses a known property of travel/lifestyle RSS feeds, where "evergreen" or "featured" articles remain pinned in the feed for months regardless of their actual publication date. Empirical testing confirmed this problem across multiple sources — for instance, the CNN Travel feed served articles from October 2022 during a January 2026 collection run (see `freshness_filtering_report.md`).

Indexed article links are persisted as JSONL files organized by source subfolder (e.g., `data/links/PUBLICO/20260115_120000.jsonl`), preserving a full provenance trail from feed to downstream processing.

### 3.2.3 Scraping Stage

Full article content is obtained using the **ScrapingBee** API, a cloud-based web scraping service that handles JavaScript rendering, proxy rotation, and anti-bot circumvention. This choice was driven by the diversity of the source portfolio: many European newspaper sites rely heavily on client-side rendering, cookie consent walls, and anti-scraping measures that would make a simple `requests.get()` approach unreliable.

Key design decisions in the scraping stage:

- **Content filtering**: Before making an API call, each article passes a `should_scrape()` gate that checks for video/podcast indicators in the URL path (e.g., `/video/`, `/cmtv/`), tags (e.g., "vídeo"), and source-specific patterns. This pre-filtering avoids wasting API credits on non-textual content.
- **Raw preservation**: The scraper saves the full raw API response (HTML/Markdown body, HTTP status, metadata) as a JSON document. The original content is never overwritten; cleaning is applied in a separate downstream stage. This decoupled design (scraper saves raw; cleaner adds a `text` field) ensures reproducibility and allows re-cleaning without re-scraping.
- **Idempotency**: Article IDs are deterministic (SHA-256 of the URL). If an article has already been scraped, it is skipped. Failed scrapes (e.g., timeouts) are logged and can be retried selectively.
- **Rate limiting**: A configurable delay (default: 1 second) between API requests avoids overloading any single source.

### 3.2.4 Source Quality Control and Removal Decisions

Not all initially configured sources proved viable. Throughout the data collection period, sources were systematically evaluated and removed when they failed to meet quality or accessibility criteria. Each removal was documented with an explicit decision record (stored in the project's `docs/` directory) to maintain full traceability. The removal categories are:

| Category | Count | Examples | Justification |
|----------|-------|----------|---------------|
| **Hard/metered paywalls** | 3 | WSJ (0% success), NYT Travel (35%), NYT World (48%) | API credits wasted on empty content |
| **Low relevance / off-topic** | 8 | Vogue US/UK (fashion-focused), Points Guy (credit-card deals), European Commission (slow institutional) | Signal-to-noise ratio too low for tourism intelligence |
| **High noise** | 1 | Telegraph (<0.1% relevant content after filtering) | Redundant with BBC/Guardian; dominated by sports/gardening |
| **Broken feeds (HTTP 404)** | 10 | UNWTO, IATA, ICAO, SIC Notícias, Lonely Planet | Feed URLs defunct at time of testing |
| **Total removed** | **34** | | |

These decisions reflect a pragmatic balance between coverage breadth and data quality, consistent with the principle that a RAG system's performance is bounded by the quality of its retrieval corpus (Lewis et al., 2020).

---

## 3.3 Data Pre-processing

### 3.3.1 Cleaning Architecture

Raw scraped content contains substantial noise: navigation menus, cookie consent banners, subscription prompts, social media share buttons, advertisement blocks, sidebar widgets, and unrelated "read next" recommendations. If this noise is embedded into the vector store, it degrades retrieval precision — a "poisoned chunk" filled with "Subscribe Now" text may match irrelevant queries. Therefore, a dedicated cleaning stage was implemented **before** chunking and embedding.

The cleaning architecture employs a **dispatcher pattern**: a central dispatcher function (`clean_and_enrich_text()`) inspects the article's `source` metadata field and routes the raw text to one of **45 source-specific cleaners**, each tailored to the HTML/Markdown structure of a particular publication. If no dedicated cleaner exists, a **generic cleaner** applies basic header trimming and inline noise removal.

Each source-specific cleaner implements a combination of the following techniques:

1. **Consent wall detection**: Articles that consist primarily of cookie consent dialogs (identified by keyword triggers such as "CookieConsent", "Responsible use of your data") are discarded entirely.
2. **Header trimming ("Title Seeker")**: The article title is located within the body text, and everything before it (typically thousands of characters of navigation menus) is removed.
3. **Footer trimming**: Text after source-specific trigger phrases (e.g., "Reportar um erro", "Subscreva", "Read more:", "Partilhar no Facebook") is truncated.
4. **Inline noise removal**: Regex patterns target advertisements, subscription CTAs, social media blocks, lottery checkers, stock tickers, podcast player UI, and related article lists.
5. **Language-specific filtering**: For multilingual sources, foreign-language advertisement blocks (e.g., English ads in Portuguese newspapers) are detected and removed using language-specific trigger phrases.

The cleaner development process was iterative: for each source, a batch of sample articles was visually inspected, noise patterns were catalogued, and cleaning rules were written and verified via a debug report that shows before/after content with character-count reduction statistics. This approach follows best practices in corpus curation for NLP pipelines (Dodge et al., 2021).

### 3.3.2 Metadata Enrichment

After cleaning, each article is enriched with structured metadata:

- **Normalized date** (`YYYY-MM-DD`): Extracted from the RSS `published` field, or from the article body if the RSS date is missing. The normalization function handles multiple date formats across languages.
- **Tags/categories**: Preserved from the RSS feed's native category fields; for some sources (e.g., ABC España, Die Zeit, Euronews), supplementary tags are extracted from the article body itself using source-specific extractors.
- **Source identifier**: A standardized uppercase source name (e.g., `PUBLICO`, `GUARDIAN_TRAVEL`) that enables downstream filtering and provenance tracking.

This metadata is stored alongside the cleaned text in the JSON document and is later injected into the vector store as chunk-level metadata, enabling filtered retrieval by source, date, or topic.

### 3.3.3 Video and Non-Article Content Filtering

The pipeline applies multiple layers of filtering to exclude non-textual content:

- **URL pattern filtering**: Articles whose URLs contain `/video/`, `/videos/`, or `/cmtv/` are skipped before scraping.
- **Tag-based filtering**: Articles tagged with "vídeo" or "videos" (case-insensitive, covering Portuguese and English) are filtered at cleaning time.
- **Empty result handling**: Articles that yield an empty string after cleaning are flagged as `is_valid_article: false` but retained on disk for audit purposes.

---

## 3.4 Knowledge Base Construction

### 3.4.1 Chunking Strategies

Long articles must be divided into smaller segments (chunks) before embedding, because (a) embedding models have a finite token limit (8,192 tokens for OpenAI's `text-embedding-3-large`), and (b) smaller chunks yield more focused semantic vectors, improving retrieval precision.

Two chunking strategies were implemented and compared:

1. **Fixed-size character chunking**: The text is split at fixed intervals (default: 2,000 characters) with a configurable overlap window (default: 200 characters). This ensures a consistent chunk size but may split mid-sentence.
2. **Recursive character splitting** (LangChain `RecursiveCharacterTextSplitter`): A hierarchical strategy that attempts to split first at paragraph boundaries (`\n\n`), then at line breaks (`\n`), then at sentence endings (`. `), and finally at word boundaries (` `). This respects natural text structure while enforcing an upper bound on chunk size.

Both strategies include an overlap window of 10–15% of the chunk size to preserve contextual continuity across chunk boundaries.

### 3.4.2 Embedding

Each text chunk is converted into a dense vector representation using OpenAI's embedding API. The project evaluates two embedding models:

| Model | Dimensions | Cost (per 1M tokens) | Quality Tier |
|-------|-----------|---------------------|-------------|
| `text-embedding-3-small` | 1,536 | $0.02 | Good |
| `text-embedding-3-large` | 3,072 (or reduced to 1,536 via Matryoshka) | $0.13 | Better |

The `text-embedding-3-large` model was selected as the primary embedding model based on OpenAI's published benchmarks (MTEB/BEIR), which show it outperforms the smaller variant on multilingual retrieval tasks — an important property for this project's seven-language corpus.

### 3.4.3 Vector Store

Embedded chunks, along with their metadata (source, date, title, tags, URL, chunk index, total chunks), are stored in **ChromaDB**, a lightweight, open-source vector database that runs locally without requiring a separate server process. ChromaDB was chosen for its simplicity, zero infrastructure overhead, and native support for metadata filtering — properties aligned with the project's goal of reproducibility and modularity.

The vector store is organized as a single collection (`tourism_knowledge`) where each entry contains:

- A deterministic chunk ID (format: `{article_hash}_chunk_{N}`)
- The embedding vector
- The original text chunk
- Metadata: `source`, `date`, `title`, `tags`, `url`, `chunk_index`, `total_chunks`

---

## 3.5 Retrieval-Augmented Generation (RAG)

### 3.5.1 Retrieval

When a user submits a query through the web interface, the system:

1. **Embeds the query** using the same embedding model used for the corpus (ensuring dimensional alignment).
2. **Performs a similarity search** against the ChromaDB collection, retrieving the top-K most semantically similar chunks (default K=10).
3. **Constructs a prompt** that presents the retrieved chunks as numbered `[Source N]` references, instructs the LLM to synthesize an answer grounded exclusively in the provided context, and requests explicit source citations.

### 3.5.2 Generation

The retrieved chunks are passed to a Large Language Model (LLM) for synthesis. The system supports multiple LLM backends including OpenAI's GPT-4o, GPT-4o-mini, and GPT-5, with automatic provider detection and fallback. The system prompt enforces:

- **Grounded answering**: The LLM must cite `[Source N]` for every claim.
- **Refusal over hallucination**: If the provided context does not contain relevant information, the LLM must explicitly state this rather than fabricate an answer.
- **Language control**: The output language is specified in the system prompt to avoid the LLM mirroring the language of Portuguese/Spanish/German chunks (a problem identified during evaluation — see Section 3.7).

### 3.5.3 Web Interface

The RAG system is served through a Flask-based web application that presents:

- A query input form
- The generated answer with source citations
- A "Retrieved Chunks" panel showing all K retrieved chunks with their metadata (source, title, date, chunk position), enabling manual verification of the retrieval quality — a design choice motivated by the traceability requirement (RQ3).

---

## 3.6 Evaluation Framework

### 3.6.1 RAG Configuration Ablation Study (RQ3)

To determine which KB structure and RAG configuration yields the best performance, a controlled ablation study was designed comparing **six configurations** that vary across three dimensions:

| Config ID | Embedding Model | Dimensions | Chunking Strategy | Chunk Size | Overlap |
|-----------|----------------|------------|-------------------|------------|---------|
| `baseline` | text-embedding-3-large | 3,072 | Fixed character | 2,000 | 200 |
| `nochunk` | text-embedding-3-large | 3,072 | None (full article) | N/A | N/A |
| `small` | text-embedding-3-large | 3,072 | Fixed character | 500 | 100 |
| `recursive` | text-embedding-3-large | 3,072 | Recursive | 2,000 | 200 |
| `small-model` | text-embedding-3-small | 1,536 | Fixed character | 2,000 | 200 |
| `reduced-dims` | text-embedding-3-large | 1,536 (reduced) | Fixed character | 2,000 | 200 |

Each configuration pair isolates a single independent variable:

| Comparison | Question Answered |
|------------|-------------------|
| `baseline` vs `nochunk` | Does chunking improve retrieval precision? |
| `baseline` vs `small` | Do smaller chunks give more precise results? |
| `baseline` vs `recursive` | Does semantically-aware splitting improve quality? |
| `baseline` vs `small-model` | Is the cheaper embedding model "good enough"? |
| `baseline` vs `reduced-dims` | Can the large model be compressed without quality loss? |
| `small-model` vs `reduced-dims` | Which is better: native small or compressed large? |

### 3.6.2 Evaluation Queries and Human Assessment

All configurations are tested against the same set of **10 standardized test queries** covering seven evaluation dimensions relevant to tourism stakeholders:

1. **Trend detection** — "What are the current trends in Portuguese tourism?"
2. **Market-specific intelligence** — "Are there emerging travel patterns from German tourists?"
3. **Competitive positioning** — "How is the Algarve positioned against competing Mediterranean destinations?"
4. **Operational signals** — "Are there any airline route changes or new flights to Portugal?"
5. **Source-market sentiment** — "What are UK travelers saying about Portugal right now?"
6. **Institutional/policy** — "What are the latest UNWTO recommendations affecting Portugal?"
7. **Luxury segment** — "How is Portugal featured in luxury travel publications?"
8. **Risk monitoring** — "Any negative news that could damage Portugal's tourism reputation?"
9. **Economic factors** — "What economic factors are affecting tourism demand in Portugal?"
10. **Cross-market comparison** — "Compare UK vs German tourist sentiment toward Portugal"

For each query, a human evaluator scores the system response on five metrics:

| Metric | Scale | Definition |
|--------|-------|------------|
| **Relevance** | 0–2 | Are the retrieved chunks relevant to the question? |
| **Completeness** | 0–2 | Does the retrieval cover the expected sources and perspectives? |
| **Precision** | 0–1 | Are there noisy or irrelevant chunks in the results? |
| **Source Utilization** | 0–2 | Did the LLM use all relevant retrieved chunks? |
| **Answer Quality** | 0–2 | Is the answer well-structured, accurate, and in the correct language? |

**Maximum score per query: 9 points. Maximum score per configuration: 90 points.**

This evaluation framework combines retrieval metrics (Relevance, Completeness, Precision) with generation metrics (Source Utilization, Answer Quality), providing a holistic assessment similar to the RAGAS framework (Es et al., 2023) but adapted for the tourism domain.

### 3.6.3 Qualitative Stakeholder Evaluation

Beyond the controlled ablation study, the system was subjected to an extended **qualitative evaluation** from a tourism stakeholder perspective (e.g., Turismo de Portugal). This evaluation assessed 11 real-world queries across dimensions including:

- **Source diversity**: Does the system retrieve from multiple source markets, or is it dominated by Portuguese publications?
- **Honest acknowledgment**: Does the LLM disclose when it cannot answer a question from the available context?
- **Query-content semantic gap**: How does query phrasing affect retrieval quality?

Findings from this evaluation directly informed pipeline improvements (e.g., cleaner refinements, identification of corpus gaps, language control in the system prompt).

---

## 3.7 Challenges and Problems Encountered

### 3.7.1 The "Garbage Chunks" Problem

Early versions of the pipeline embedded raw scraped content without cleaning, resulting in vector representations polluted by navigation menus, advertisements, and subscription prompts. These "garbage chunks" were semantically similar to broad queries (e.g., a footer containing "Travel News | UK | Portugal" matched queries about UK travel to Portugal) and degraded retrieval precision. The solution was the source-specific cleaning architecture described in Section 3.3.1, which required iterative development across 45+ source-specific cleaners.

### 3.7.2 Source Dominance and Retrieval Bias

The `nochunk` configuration (full-article embeddings) revealed a critical issue: Portuguese-language sources, particularly `Público Turismo`, dominated retrieval results because their articles are long, keyword-dense, and semantically close to many Portugal-related queries. In one evaluation (Q1: "What are current trends in Portuguese tourism?"), all 10 retrieved chunks came from a single source, achieving zero source diversity. This finding (documented in the `nochunk` evaluation, Q1) directly motivated the chunking approach, which distributes retrieval across more diverse chunks.

### 3.7.3 Language Mirroring in LLM Output

During the Q4 evaluation ("Are there any airline route changes or new flights to Portugal?"), the LLM generated its answer in Portuguese rather than English because all 10 retrieved chunks were Portuguese-language articles. This was resolved by adding explicit language control in the system prompt, a solution also recommended in multilingual RAG literature (Shi et al., 2024).

### 3.7.4 Query-Content Semantic Gap

A significant finding was the "query-content semantic gap" problem: the embedding similarity function matches on topical content, NOT on meta-level constraints like source origin or query framing. For example, the query "What competing destinations are being promoted as alternatives to Portugal?" (Test 6) retrieved zero competitor information, while the semantically equivalent but differently phrased "What touristic destinations are trending?" (Test 7) successfully retrieved 9 out of 10 international sources with extensive competitor data. This finding has implications for both system design (motivating query expansion and metadata-filtered retrieval) and user guidance.

### 3.7.5 Paywall and Cookie Consent Walls

Several sources (WSJ, NYT) proved inaccessible due to hard or metered paywalls, resulting in wasted API credits and empty articles. Additionally, some European sources (particularly GDPR-compliant sites) returned cookie consent dialogs instead of article content. These were addressed through (a) empirical testing and removal of consistently failing paywalled sources, and (b) automated consent wall detection at cleaning time.

---

## 3.8 Ethical Considerations and Data Privacy

### 3.8.1 Data Collection Ethics

All data is collected from **publicly available RSS feeds** — a syndication protocol explicitly designed by publishers for third-party consumption. No login credentials, paywall circumvention, or ToS-violating scraping techniques are employed. The ScrapingBee API handles standard web access (rendering, proxying) but does not bypass access controls.

### 3.8.2 Personal Data

The corpus consists of published news articles. While articles may mention public figures (politicians, business executives), no personal data of private individuals is processed. Author names from article bylines are stored as metadata for provenance purposes only, consistent with the journalistic publication context.

### 3.8.3 Provenance and Traceability

Every piece of information in the system can be traced back to its original source. The pipeline preserves: (a) the original RSS entry metadata, (b) the raw scraped content, (c) the cleaned text, (d) the chunk boundaries and chunk-level metadata, and (e) the source citations in LLM-generated answers. This end-to-end traceability is a core design principle, directly addressing RQ3's focus on traceability.

### 3.8.4 LLM Usage and Hallucination Mitigation

The system uses third-party LLM APIs (OpenAI) for embedding and generation. To mitigate hallucination risk, the system prompt explicitly instructs the LLM to refuse to answer rather than fabricate information when the provided context is insufficient. The "Retrieved Chunks" transparency panel in the web interface allows human verification of every claim.

---

## 3.9 Technology Stack Summary

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Language** | Python 3.x | Ecosystem maturity for NLP/ML tasks |
| **RSS Parsing** | `feedparser` | Industry-standard RSS/Atom parser |
| **Web Scraping** | ScrapingBee API | Handles JS rendering, proxies, anti-bot measures |
| **Text Cleaning** | Custom Python (regex) | 45 source-specific cleaners; no generic solution exists |
| **Text Chunking** | Custom + LangChain `RecursiveCharacterTextSplitter` | Semantic boundary-aware splitting |
| **Embeddings** | OpenAI `text-embedding-3-large` | SOTA multilingual performance (MTEB/BEIR) |
| **Vector Database** | ChromaDB | Lightweight, local, metadata-filtered search |
| **LLM (Generation)** | OpenAI GPT-4o / GPT-4o-mini / GPT-5 | Multilingual reasoning, instruction following |
| **Web Interface** | Flask + Jinja2 | Minimal overhead for research prototype |
| **Orchestration** | Makefile | Reproducible pipeline execution with single commands |

All components are modular: each pipeline stage reads from and writes to files or databases, with no hard coupling. The entire pipeline can be re-executed from any stage without re-running upstream stages.

---

## 3.10 Relation to Prior Work

The pipeline architecture draws on and extends several threads in the literature:

- **News-driven tourism forecasting**: Park et al. (2021) and Chen et al. (2024) demonstrated that news signals improve forecasting accuracy. This project operationalizes their insight by building a continuous ingestion pipeline rather than using static historical datasets.
- **Tourism-aware NLP systems**: CTourLLM (Wei et al., 2025) and TravelRAG (Song et al., 2024) are recent examples of domain-specific RAG for tourism. However, neither operates on multilingual, multi-market news streams at the scale attempted here (57 feeds, 7 languages, 45 source-specific cleaners).
- **RAG architecture**: The retrieve-then-generate paradigm follows Lewis et al. (2020). The chunking, embedding, and retrieval evaluation methodology is informed by RAGAS (Es et al., 2023) and adapted for sector-specific evaluation.
- **Big-data tourism analytics**: Wu et al. (2025) call for high-frequency textual intelligence systems; Núñez et al. (2024) highlight generalization and explainability challenges in ML-based tourism forecasting. This project addresses both by providing source-grounded, transparent answers with full citation provenance.
- **Knowledge Base construction**: Caddedu et al. (2024) note that structured tourism KBs remain emerging. This project contributes a reproducible architecture for automatically constructing a tourism KB from continuous news streams, with explicit governance (provenance, freshness filtering, quality control).

---

## 3.11 What This Section Does NOT Include

Consistent with methodological conventions, this section describes the design, materials, and procedures of the research but does **not** present results. Evaluation outcomes, performance comparisons across the six RAG configurations, and findings from the qualitative stakeholder evaluation are presented in Chapter 4 (Results) and discussed in Chapter 5 (Discussion).


The methodology section draft has been written. Let me now give you a structured walkthrough of what it covers and what's still missing.

✅ What the Draft Covers
I wrote 11 subsections based on a deep read of your entire codebase, documentation, and evaluation logs:

Section	Content	Maps to RQ
3.1 Overview & Research Design	DSR approach, three-phase framework, RQ-to-phase mapping, placeholder for a research design diagram	All
3.2 Data Collection	Source selection (57 feeds, 7 languages), indexing (feedparser, freshness filtering, fingerprinting), scraping (ScrapingBee, raw preservation, idempotency), source quality control (34 removed sources with justification)	RQ1
3.3 Data Pre-processing	Cleaning architecture (dispatcher + 45 source-specific cleaners), metadata enrichment, video/non-article filtering	RQ1
3.4 KB Construction	Two chunking strategies (fixed-size + recursive), embedding models compared, ChromaDB vector store with metadata schema	RQ3
3.5 RAG	Retrieval (query embedding → similarity search → prompt construction), generation (grounding, refusal, language control), web interface with traceability panel	RQ1/RQ3
3.6 Evaluation Framework	6-config ablation study (exact configs from your 
chunking_embedding_evaluation.md
), 10 test queries, 5-metric human scoring, qualitative stakeholder evaluation	RQ3
3.7 Challenges	Garbage chunks, source dominance, language mirroring, query-content semantic gap, paywall/consent walls — all drawn from your actual evaluation logs	All
3.8 Ethics & Data Privacy	RSS as public syndication, no personal data, provenance/traceability, hallucination mitigation	—
3.9 Technology Stack	Complete table with justifications for each tool	—
3.10 Relation to Prior Work	Maps your pipeline to Park et al., CTourLLM, TravelRAG, RAGAS, Wu et al., Núñez et al.	All


🔴 What Is Missing / Needs Your Input
Here are things I flagged as gaps or items only you can provide:

1. Research Design Diagram (Figure 3.1)
I left a placeholder (<!-- TODO -->) for a visual research design diagram. This is highly recommended by your dissertation structure requirements. It should show the flow from source markets → RSS feeds → pipeline stages → KB → RAG → dashboard, with the three phases and RQs bracketed around the relevant stages.

2. Phase 2 — Classification (RQ2)
Your one-pager mentions a "tourism-aware classifier" that assigns items to categories (regulatory change, transport disruption, safety/macro, image/reputation) and tags risk/opportunity. However, I found no implemented classifier in the codebase — only design notes in 
RESEARCH_ROADMAP.md
 and 
rag_improvements.md
 listing options (GPT-4o-mini vs. DeBERTa zero-shot). Is this component built yet? If not, the methodology should describe the planned approach and evaluation protocol. If it is, I need to see the code to describe it accurately.

3. Exact Corpus Statistics
The draft would benefit from precise numbers. Could you confirm:

Total number of articles scraped (I saw ~4,492 in the build stats)?
Total number successfully cleaned and embedded?
Date range of the corpus (first article date to last)?
Total number of chunks in the final vector store?
4. Machine Translation
Your one-pager mentions "machine-translated if needed" — but I didn't find any translation stage in the pipeline. Articles appear to be embedded in their original language. Is this intentional (relying on the multilingual capabilities of the embedding model), or is translation planned but not yet implemented?

5. Wikipedia Component
The pipeline includes a 
04__wiki_fetcher.py
 for Wikipedia articles, and the web app has --use-wikipedia / --no-wikipedia flags. Should this be mentioned in the methodology, or has it been deprecated?

6. Dashboard / BI Integration
Your one-pager mentions a "dashboard for traceable alerts" and "API that integrates with BI tools". Currently, you have a Flask web interface — is there a separate dashboard component, or is the web app the dashboard?

7. Your Reference List
I mentioned several papers (Hevner et al., Park et al., etc.) but didn't have your full bibliography. You'll need to ensure the references match your actual reference list.

