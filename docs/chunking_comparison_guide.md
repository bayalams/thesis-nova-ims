# Chunking Method Comparison Guide

This guide helps you test different chunking strategies before re-embedding your entire database.

## Quick Start

### 1. Create Test Database with Recursive Chunking
```bash
python experiments/chunking_test/10b__embedder_test.py --sample 50 --method recursive
```

This will:
- Sample 50 random articles from `data/articles/`
- Chunk them using **Recursive Character Chunking** (smart boundaries)
- Create embeddings and store in `data/vectordb_test/`
- Cost: ~$0.05-0.10 (only 50 articles)

### 2. Query the Test Database
```bash
python 11b__web_app_test.py
```

Open: http://localhost:9998

### 3. Compare Side-by-Side

**Main Database** (Fixed Chunking):
- Run: `python 11__web_app.py`
- Open: http://localhost:9999

**Test Database** (Recursive Chunking):
- Run: `python experiments/chunking_test/11b__web_app_test.py`
- Open: http://localhost:9998

Ask the **same question** in both apps and compare:
- Are the retrieved chunks more coherent in the test DB?
- Does it retrieve more relevant sources?
- Are sentences/paragraphs kept intact?

---

## Evaluation Criteria

For each test query, compare:

| Metric | Fixed Chunking (Main) | Recursive Chunking (Test) | Winner |
|--------|----------------------|---------------------------|--------|
| **Coherence** | Chunks cut mid-sentence? | Chunks end at natural boundaries? | |
| **Relevance** | How many of 5 chunks are useful? | How many of 5 chunks are useful? | |
| **Source Coverage** | Did it find expected sources? | Did it find expected sources? | |

---

## Decision Matrix

### ✅ Switch to Recursive Chunking if:
- Test DB retrieves **more relevant chunks** (higher Precision)
- Test DB finds **more expected sources** (higher Recall)
- Chunks are **more readable** (no mid-sentence cuts)

### ❌ Keep Fixed Chunking if:
- No significant difference in retrieval quality
- Test DB performs **worse** (unlikely, but possible)

---

## How to Apply the Winner

If Recursive Chunking wins:

1. **Update `10__embedder.py`**:
   - Replace the `chunk_text()` function with `chunk_text_recursive()` from `10b__embedder_test.py`

2. **Re-embed Full Database**:
   ```bash
   python 10__embedder.py
   ```
   
   This will:
   - Delete the old database
   - Re-chunk all articles using recursive method
   - Re-embed everything (~$1-2 for 1000 articles)

3. **Verify**:
   ```bash
   python inspect_db.py
   ```

---

## Testing Different Methods

You can also test **Fixed** chunking on the sample to establish a baseline:

```bash
# Test fixed chunking
python 10b__embedder_test.py --sample 50 --method fixed

# Query it
python 11b__web_app_test.py
```

This creates an apples-to-apples comparison on the same 50 articles.

---

## Cost Estimate

| Sample Size | Chunks (est.) | Embedding Cost |
|-------------|---------------|----------------|
| 50 articles | ~250 chunks   | $0.05          |
| 100 articles| ~500 chunks   | $0.10          |
| 500 articles| ~2,500 chunks | $0.50          |

**Full re-embedding** (all articles): $1-3 depending on total count.
