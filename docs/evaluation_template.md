# Tourism Intelligence System - Evaluation Template

**Date:** _________  
**Evaluator:** _________  
**System Version:** _________

---

## Scoring Guide

For each test query, evaluate the system's response across three dimensions:

### **Source Accuracy** (Did it cite the right feeds?)
- ✅ **Good (2)**: Retrieved articles from expected sources
- ⚠️ **Partial (1)**: Retrieved some relevant sources, missed key ones
- ❌ **Bad (0)**: Retrieved wrong sources or no sources

### **Answer Quality** (Was the synthesis useful?)
- ✅ **Good (2)**: Clear, actionable insights with proper citations
- ⚠️ **Partial (1)**: Correct but vague, or missing context
- ❌ **Bad (0)**: Hallucination, contradictory, or "I don't know" when data exists

### **Freshness** (Is the data recent?)
- ✅ **Good (1)**: Articles from last 7 days
- ⚠️ **Partial (0.5)**: Articles from last 30 days
- ❌ **Bad (0)**: Articles older than 30 days

---

## Advanced Metrics: Precision & Recall

For a more rigorous evaluation, calculate **Precision** and **Recall** for retrieval quality.

### **How to Calculate**

For each query, the system retrieves **K chunks** (typically K=5). You need to manually judge:
- **Relevant**: How many of the K retrieved chunks actually help answer the question?
- **Total Relevant in DB**: How many relevant chunks exist in the entire database for this query?

#### **Precision** = (Relevant Retrieved) / (Total Retrieved)
*"Of what the system showed me, how much was useful?"*

**Example:**
- System retrieved 5 chunks
- 3 were relevant, 2 were noise
- **Precision = 3/5 = 60%**

#### **Recall** = (Relevant Retrieved) / (Total Relevant in DB)
*"Of all the useful info available, how much did the system find?"*

**Example:**
- You know there are 8 relevant articles in the database
- System only retrieved 3 of them
- **Recall = 3/8 = 37.5%**

### **Practical Shortcut**

Since you can't manually check the entire database for every query, use this approximation:

**Precision**: Easy to measure (just look at the 5 results)  
**Recall**: Estimate by checking if **all expected sources** (from the "Expected Sources" column) appear in the results.

- If all expected sources cited → **High Recall (~80-100%)**
- If 1-2 missing → **Medium Recall (~50-70%)**
- If most missing → **Low Recall (<50%)**

### **Target Metrics**
- **Precision**: >70% (most results should be relevant)
- **Recall**: >60% (shouldn't miss major sources)

---

### **Precision/Recall Tracking (Optional)**

Use this table to track P/R for a subset of queries:

| Query # | Retrieved Chunks | Relevant Chunks | Precision | Expected Sources | Sources Found | Recall Estimate |
|---------|------------------|-----------------|-----------|------------------|---------------|-----------------|
| 1       | 5                |                 | %         | 3                |               | %               |
| 8       | 5                |                 | %         | 2                |               | %               |
| 12      | 5                |                 | %         | 2                |               | %               |

**Average Precision:** ___%  
**Average Recall:** ___%

**Maximum Score per Query:** 5 points  
**Target Overall Score:** 70%+ (87.5/125 points)

---

## Test Results

### 1. Trend Detection & Analysis

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 1 | "What are the current trends in Portuguese tourism based on recent news?" | PUBLICO, RTP, OBSERVADOR | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 2 | "Are there any emerging travel patterns from German tourists to Portugal?" | SPIEGEL_REISE, SUEDDEUTSCHE_REISE, TOURISTIK_AKTUELL | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 3 | "What economic factors are currently affecting tourism demand in Portugal?" | ECO_ONLINE, JORNAL_NEGOCIOS, JORNAL_ECONOMICO | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 4 | "How is the winter season performing compared to last year?" | PUBLITURIS, AMBITUR, HOSTELTUR | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/20

---

### 2. Competitive Intelligence

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 5 | "What is Spain doing differently in tourism marketing compared to Portugal?" | EL_PAIS, ABC_ESPANA, HOSTELTUR | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 6 | "How is the Algarve positioned against competing Mediterranean destinations?" | PUBLITURIS, SKIFT, TRAVEL_LEISURE | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 7 | "What new tourism initiatives has Spain announced recently?" | EL_PAIS_ECONOMIA, EL_PAIS_ESPANA | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/15

---

### 3. Market-Specific Insights

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 8 | "What are UK travelers saying about Portugal right now?" | BBC_TRAVEL, GUARDIAN_TRAVEL | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 9 | "Are there any concerns about Portugal in US travel media?" | NYT_TRAVEL, CNN_TRAVEL, CNBC_TRAVEL | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 10 | "What French tourism trade publications are reporting about Portugal?" | TOURMAG, LECHO_TOURISTIQUE | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 11 | "What are German sources saying about Portugal travel?" | SPIEGEL_REISE, SUEDDEUTSCHE_REISE | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/20

---

### 4. Operational & Supply Signals

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 12 | "Are there any airline route changes or new flights to Portugal?" | ANA_AEROPORTOS, SIMPLE_FLYING | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 13 | "What aviation disruptions could impact Portuguese tourism this month?" | SIMPLE_FLYING, IATA, ICAO | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 14 | "What is ANA Aeroportos reporting about passenger traffic?" | ANA_AEROPORTOS | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/15

---

### 5. Policy & Institutional

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 15 | "What are the latest UNWTO recommendations that could affect Portugal?" | UNWTO | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 16 | "Are there any new EU tourism regulations or initiatives?" | EUROPEAN_COMMISSION, EUROSTAT | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 17 | "What is Eurostat showing about tourism statistics in Portugal?" | EUROSTAT | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/15

---

### 6. Luxury & High-Value Segment

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 18 | "How is Portugal being featured in luxury travel publications like Vogue?" | VOGUE_US_TRAVEL, VOGUE_UK_TRAVEL | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 19 | "What high-end travel experiences in Portugal are getting media attention?" | CONDE_NAST_TRAVELER, VOGUE_US_TRAVEL | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 20 | "List the 'best hotels' in Portugal recently mentioned by international press." | CONDE_NAST_TRAVELER, TRAVEL_LEISURE | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/15

---

### 7. Crisis & Risk Monitoring

| # | Query | Expected Sources | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|------------------|-----------------|----------------|-----------|-------|-------|
| 21 | "Are there any negative news stories that could damage Portugal's tourism reputation?" | PUBLICO, BBC, GUARDIAN | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 22 | "What economic challenges are tourists from key markets facing?" | ECO_ONLINE, NYT_WORLD, GUARDIAN | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 23 | "Are there any strikes, protests, or disruptions affecting Portuguese tourism?" | RTP_NOTICIAS, SIC_NOTICIAS, PUBLICO | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/15

---

### 8. Edge Cases & Failure Modes

| # | Query | Expected Behavior | Source Accuracy | Answer Quality | Freshness | Total | Notes |
|---|-------|-------------------|-----------------|----------------|-----------|-------|-------|
| 24 | "What is the tourism impact of cork exports?" | Should say "no direct data" or cite economic sources | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |
| 25 | "Compare UK vs German tourist sentiment toward Portugal" | Should cite both UK and German sources | ☐ 2 ☐ 1 ☐ 0 | ☐ 2 ☐ 1 ☐ 0 | ☐ 1 ☐ 0.5 ☐ 0 | /5 | |

**Subtotal:** ___/10

---

## Final Score

**Total Points:** ___/125  
**Percentage:** ___%  

### Performance Rating
- **90-100% (112.5-125 pts)**: Excellent - Production ready
- **70-89% (87.5-112 pts)**: Good - Minor improvements needed
- **50-69% (62.5-87 pts)**: Fair - Significant issues to address
- **<50% (<62.5 pts)**: Poor - Major redesign required

---

## Key Findings

### Strengths
1. 
2. 
3. 

### Weaknesses
1. 
2. 
3. 

### Recommended Actions
1. 
2. 
3. 

---

## Notes & Observations

