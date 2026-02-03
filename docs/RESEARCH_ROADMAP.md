# Tourism Intelligence Project Roadmap
*From Raw News to Actionable Insights*

This roadmap maps your research proposal (RQ1, RQ2, RQ3) to concrete technical tasks.

---

##  PHASE 1: Data Foundations (Solving RQ1)
*Objective: Transform continuous noise into clean, verifiable signal.*

**Current Status:** 🚧 BLOCKED by "Garbage Chunks" (Navigation links, ads, noise).

### ✅ 1.1 Source Expansion (Complete)
- [x] Integrate RSS feeds (Economy, Aviation, Regional)
- [x] Add key markets (Germany, France, UK, US, Spain)

### 🚧 1.2 Data Cleaning & Enrichment (IMMEDIATE PRIORITY)
**Goal:** Ensure the system ingests *news*, not *websites*.
- [ ] **Implement Text Cleaner**: Create regex filters to strip navigation menus, "Read more" links, and image alt text.
- [ ] **Metadata Extraction**: reliably extract `Publication Date` and `Tags` from HTML.
- [ ] **Context Injection**: Prepend Date/Tags to every text chunk so chunks are self-contained.
- [ ] **Validation**: Use "Retrieved Chunks" view to prove content is 95%+ pure signal.

### 📅 1.3 Chunking Strategy
- [ ] **Finalize Chunking**: Text vs Recursive? (Test with clean data).
- [ ] **Re-index Corpus**: Run the cleaner + embedder on the full dataset.

---

## PHASE 2: Intelligence Layer (Solving RQ2)
*Objective: Classify news into actionable categories (Risk, Opportunity, Neutral).*

### 🤖 2.1 Automated Classification
- [ ] **Design Taxonomy**: Define what "Risk" looks like (Strike, Bankruptcy) vs "Opportunity" (New Route, Award).
- [ ] **Implement Classifier**: 
    - *Option A*: Cheap LLM (GPT-4o-mini) step during ingestion.
    - *Option B*: Zero-shot classifier (DeBERTa model) locally.
- [ ] **Store Classification**: Add `category` and `sentiment` to ChromaDB metadata.

### ⏱️ 2.2 Freshness & Alerts
- [ ] **Date Filtering**: Enable specific query filters (e.g., "News from last 7 days").
- [ ] **Alert Logic**: "If Risk detected in Source Market UK -> Trigger Alert."

---

## PHASE 3: System Optimization (Solving RQ3)
*Objective: Improve accuracy, traceability, and latency.*

### 🔍 3.1 Retrieval Evaluation
- [ ] **Metric Tracking**: Measure Precision/Recall using `evaluation_template.md`.
- [ ] **Latency Optimization**: Ensure answers generate in <5 seconds.

### 📊 3.2 Dashboard & Reporting
- [ ] **Weekly Report Generator**: Script to pull "Top 10 High-Impact Events" regardless of user query.
- [ ] **Web UI Upgrade**: Show "Latest Risks" and "Market Trends" on homepage.

---

## IMMEDIATE NEXT STEPS

1.  **Fix the Data**: Write the `clean_text()` function in `experiments/chunking_test`.
2.  **Test Cleaning**: Verify that `experiments/chunking_test` output looks readable.
3.  **Apply to Main**: Port the cleaner to `10__embedder.py` and re-embed.
