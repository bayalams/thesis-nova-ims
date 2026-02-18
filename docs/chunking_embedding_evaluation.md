# Chunking & Embedding Configuration Evaluation

**Date:** February 2026  
**Objective:** Compare 6 retrieval configurations to find the optimal chunking strategy and embedding model for the Tourism Intelligence RAG system.

---

## Configurations Under Test

| # | ID | Embedding Model | Dims | Chunking | Chunk Size | Overlap | DB Directory | Status |
|---|---|---|---|---|---|---|---|---|
| 0 | `baseline` | text-embedding-3-large | 3072 | Character | 2000 | 200 | `vectordb_azure` | ✅ Done |
| 1 | `nochunk` | text-embedding-3-large | 3072 | None | Full article | N/A | `vectordb_nochunk` | ✅ Done |
| 2 | `small` | text-embedding-3-large | 3072 | Character | 500 | 100 | `vectordb_small_chunks` | ☐ |
| 3 | `recursive` | text-embedding-3-large | 3072 | Recursive | 2000 | 200 | `vectordb_recursive` | ☐ |
| 4 | `small-model` | text-embedding-3-small | 1536 | Character | 2000 | 200 | `vectordb_small_model` | ☐ |
| 5 | `reduced-dims` | text-embedding-3-large | 1536 | Character | 2000 | 200 | `vectordb_large_reduced` | ☐ |

### Commands
```bash
# Already done:
# make embed PROVIDER=azure

# To run:
make embed-test-nochunk PROVIDER=azure
make embed-test-small PROVIDER=azure
make embed-test-recursive PROVIDER=azure
make embed-test-small-model PROVIDER=azure
make embed-test-reduced-dims PROVIDER=azure
```

---

## Build Statistics

Record these after each embedding run.

| Config | Total Docs | Embedded | Skipped (too long) | Total Chunks | DB Size (MB) | Build Time |
|---|---|---|---|---|---|---|
| baseline | 4492 | 2504 | 0 | 7452 | 225 | |
| nochunk | 4492 | 3809 | 683 | 3809 | 202 | |
| small | | | 0 | | | |
| recursive | | | 0 | | | |
| small-model | | | 0 | | | |
| reduced-dims | | | 0 | | | |

> **Note:** The "Skipped (too long)" column is especially important for `nochunk` — it shows how many articles exceed the 8,192 token embedding limit and therefore can't be embedded without chunking.

---

## Evaluation Methodology

Each configuration is tested with the **same 10 queries** (subset from `test_queries.md`). For each query, evaluate:

### Retrieval Metrics
- **Relevance (0-2):** Are the retrieved chunks relevant to the question?
- **Completeness (0-2):** Does the retrieval cover expected sources/perspectives?
- **Precision (0-1):** Are there noisy/irrelevant chunks in the results?

### LLM Response Metrics
- **Source Utilization (0-2):** Did the LLM use all relevant retrieved chunks? (0 = used few, 1 = used some, 2 = used all relevant)
- **Answer Quality (0-2):** Is the answer well-structured, accurate, and in the correct language?

**Max score per query: 9 | Max score per config: 90**

### Selected Test Queries

| Q# | Query | Expected Sources |
|---|---|---|
| 1 | "What are the current trends in Portuguese tourism?" | PUBLICO, RTP, OBSERVADOR |
| 2 | "Are there emerging travel patterns from German tourists?" | SPIEGEL_REISE, SUEDDEUTSCHE_REISE |
| 3 | "How is the Algarve positioned against competing Mediterranean destinations?" | PUBLITURIS, SKIFT |
| 4 | "Are there any airline route changes or new flights to Portugal?" | ANA_AEROPORTOS, SIMPLE_FLYING |
| 5 | "What are UK travelers saying about Portugal right now?" | BBC_TRAVEL, GUARDIAN_TRAVEL |
| 6 | "What are the latest UNWTO recommendations affecting Portugal?" | UNWTO |
| 7 | "How is Portugal featured in luxury travel publications?" | VOGUE_US_TRAVEL, CONDE_NAST_TRAVELER |
| 8 | "Any negative news that could damage Portugal's tourism reputation?" | PUBLICO, BBC, GUARDIAN |
| 9 | "What economic factors are affecting tourism demand in Portugal?" | ECO_ONLINE, JORNAL_NEGOCIOS |
| 10 | "Compare UK vs German tourist sentiment toward Portugal" | BBC_TRAVEL, SPIEGEL_REISE |

---

## Results

### Config 0: `baseline` (2000 char / 200 overlap / 3-large)

| Q# | Rel. | Compl. | Prec. | Src Use | Ans Qual. | Total | Notes |
|---|---|---|---|---|---|---|---|
| 1 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 2 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 3 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 4 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 5 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 6 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 7 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 8 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 9 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 10 | /2 | /2 | /1 | /2 | /2 | /9 | |
| **Total** | | | | | | **/90** | |

---

### Config 1: `nochunk` (no chunking / 3-large)

| Q# | Rel. | Compl. | Prec. | Src Use | Ans Qual. | Total | Notes |
|---|---|---|---|---|---|---|---|
| 1 | 2/2 | 1/2 | 0/1 | 1/2 | 2/2 | 6/9 | All 10 from publico_turismo. LLM used 5/10. Good synthesis but no source diversity. |
| 2 | 1/2 | 0/2 | 0/1 | 1/2 | 1/2 | 3/9 | No German sources. LLM admits lack of data, resorts to inference. 4/10 used. |
| 3 | 2/2 | 1/2 | 1/1 | 1/2 | 2/2 | 7/9 | Strong Algarve coverage. LLM answer quality high but only cited 5/10 relevant chunks. |
| 4 | 2/2 | 2/2 | 1/1 | 1/2 | 1/2 | 7/9 | All 10 chunks relevant. LLM only cited 5/10. ⚠️ Answer in Portuguese — LLM mirrored chunk language. |
| 5 | 1/2 | 0/2 | 0/1 | 1/2 | 1/2 | 3/9 | Only 2-3 relevant chunks (Condé Nast UK). 7/10 about Brazilian/Portuguese travel. LLM missed Chunk #6 (Condé Nast hotels). |
| 6 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 7 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 8 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 9 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 10 | /2 | /2 | /1 | /2 | /2 | /9 | |
| **Total** | | | | | | **/90** | |

#### Q1 Detailed Analysis: "What are the current trends in Portuguese tourism?"

**Retrieved chunks (10/10 from `publico_turismo` only):**

| Chunk | Title | Used? |
|---|---|---|
| 1 | Turismo volta a bater recorde, com mais de 18 milhões de hóspedes até Julho | ✅ |
| 2 | Concelho de Lisboa concentrou 28% do total dos hóspedes registados em 2024 | ✅ |
| 3 | Portugueses viajam mais no fim de ano. Em alta: Madeira e Algarve, Cabo Verde e Brasil | ✅ |
| 4 | Receitas com hóspedes até Novembro superaram as de 2023 inteiro | ✅ |
| 5 | Portugal faz campanha para atrair turistas brasileiros tendo a arte como estrela | ✅ |
| 6 | Polónia e Canadá puxam por subida de turistas estrangeiros no trimestre | ❌ |
| 7 | Portugal está caro e os portugueses fazem cada vez mais férias lá fora | ❌ |
| 8 | Portugueses são os turistas que mais tempo passam no Brasil: 18 dias, em média | ❌ |
| 9 | Turismo e Vinhos de Portugal no Brasil juntam-se na promoção do enoturismo | ❌ |
| 10 | Crescimento do turismo foi superior ao do resto da economia | ❌ |

**Key findings:**
- **Source diversity: ZERO** — all 10 chunks from `publico_turismo`. Missing RTP and OBSERVADOR entirely.
- **Precision: 50%** — 5/10 chunks used. Unused chunks were tangential (Brazil tourism, wine tourism, Polish tourists).
- **Answer quality was high** despite retrieval issues — GPT-5 synthesized well from the 5 relevant articles.
- **No-chunk weakness:** Full articles are long and keyword-dense, so Público articles dominate similarity search, crowding out other sources.

#### Q2 Detailed Analysis: "Are there emerging travel patterns from German tourists?"

**Retrieved chunks (sources: BREAKING_TRAVEL_NEWS, ETURBONEWS ×4, FAZ, GUARDIAN_GENERAL):**

| Chunk | Title | Source | Used? |
|---|---|---|---|
| 1 | Overseas Travellers Turn to New European Destinations | BREAKING_TRAVEL_NEWS | ✅ |
| 2 | Bulgarians Travel More, Farther, and Longer | ETURBONEWS | ❌ |
| 3 | Mega Baltic Sea Resort Set to Open in 2026 | ETURBONEWS | ✅ |
| 4 | Europe vs. the USA in 2026: Why the "Trump Factor" | ETURBONEWS | ✅ |
| 5 | Fraport Reports Strong January Growth | ETURBONEWS | ✅ |
| 6 | Tourismus in Frankfurt: Gäste bringen fast fünf Milliarden Euro | FAZ | ❌ |
| 7 | Spain Emerges as World's Tourism Powerhouse | ETURBONEWS | ❌ |
| 8 | Europeans shunning US as Emirates and Asia travel prove popular | GUARDIAN_GENERAL | ❌ |
| 9 | Guernsey vs. the Mediterranean | ETURBONEWS | ❌ |
| 10 | The Dean Berlin Opens | ETURBONEWS | ❌ |

**Key findings:**
- **Expected sources completely absent** — SPIEGEL_REISE and SUEDDEUTSCHE_REISE not retrieved at all.
- **Answer quality: weak** — LLM explicitly admits "the sources do not give detailed, Germany-specific data" and resorts to inference.
- **Precision: 40%** — 4/10 used. Irrelevant chunks include Bulgarian tourism, Guernsey island tourism, a Berlin hotel opening.
- **HTML noise problem** — full articles include navigation menus, cookie banners, ad blocks, sidebar content. The no-chunk approach embeds all this noise.
- **Worst score so far** — this query exposes the no-chunk config's inability to surface niche/specific sources.

#### Q3 Detailed Analysis: "How is the Algarve positioned against competing Mediterranean destinations?"

**Retrieved chunks (sources: publico_turismo ×4, AMBITUR ×2, TOURMAG ×1):**

| Chunk | Title | Source | Used? |
|---|---|---|---|
| 1 | Ocupação hoteleira no Algarve quebrou 0,5% em Agosto | publico_turismo | ✅ |
| 2 | Destino Nacional Convidado BTL 2026: Algarve diverso e competitivo | AMBITUR | ✅ |
| 3 | As caminhadas no Algarve são uma aposta ganha | publico_turismo | ✅ |
| 4 | Algarve teve mais turistas portugueses hospedados em Agosto | publico_turismo | ✅ |
| 5 | Verdelago é finalista do MIPIM Awards | AMBITUR | ✅ |
| 6 | Portugal é o "Melhor Destino de Golfe do Mundo" | publico_turismo | ❌ |
| 7 | World Travel Awards: Madeira, Açores, Algarve | publico_turismo | ❌ |
| 8 | AlgarExperience: 2026 traz novidades | AMBITUR | ❌ |
| 9 | Mais de dois terços dos vinhos do Algarve vendidos na região | publico_turismo | ❌ |
| 10 | Madère consolide sa position sur le marché français | TOURMAG | ❌ |

**Key findings:**
- **Best nochunk result so far** — 5/5 used chunks were directly relevant to Algarve competitive positioning.
- **Missing expected sources** — PUBLITURIS and SKIFT not retrieved. No international competitive benchmarking perspective.
- **Answer quality: strong** — covered hotel occupancy, strategic branding (BTL 2026), nature diversification, tourism stats, and international recognition (MIPIM).
- **Unused chunks still Algarve-adjacent** — golf awards, wine, experiences, WTA — not completely random noise like Q2.
- **No direct competitor comparison** — answer acknowledges lack of "direct comparative data with specific competitors."

#### Q4 Detailed Analysis: "Are there any airline route changes or new flights to Portugal?"

**Retrieved chunks (sources: publico_turismo ×8, AMBITUR ×1):**

| Chunk | Title | Source | Used? |
|---|---|---|---|
| 1 | easyJet: Porto–Split, Funchal–Nantes | publico_turismo | ✅ |
| 2 | Play estreia rota Funchal–Reiquejavique | publico_turismo | ✅ |
| 3 | TAP nova rota Lisboa–São Luís | AMBITUR | ✅ |
| 4 | Ryanair: sem crescimento em Lisboa, taxas excessivas | publico_turismo | ✅ |
| 5 | Azul: nova rota Recife–Porto | publico_turismo | ✅ |
| 6 | Novos voos para o Brasil esbarram em limites em Lisboa | publico_turismo | ❌ |
| 7 | easyJet estreia voos para Cabo Verde | publico_turismo | ❌ |
| 8 | LATAM voo direto Fortaleza–Lisboa | publico_turismo | ❌ |
| 9 | Efeito Trump: europeus cortam viagens para EUA | publico_turismo | ❌ |
| 10 | airBaltic: Funchal–Riga | publico_turismo | ❌ |

**Key findings:**
- **Perfect topical retrieval** — all 10 chunks are about flight routes involving Portugal. Cabo Verde, Riga, LATAM Fortaleza, slot limitations — all directly relevant.
- **LLM under-cited** — only 5/10 cited, but this is a generation issue, not retrieval. All 10 chunks provided useful aviation context.
- **Missing expected sources** — ANA_AEROPORTOS and SIMPLE_FLYING absent, but coverage was comprehensive regardless.
- **⚠️ Language issue discovered** — Answer came in Portuguese because all chunks were Portuguese. System prompt should enforce English output.
- **publico_turismo monopoly** — 8/10 chunks from one source, crowding out English aviation sources.

#### Q5 Detailed Analysis: "What are UK travelers saying about Portugal right now?"

**Retrieved chunks (sources: publico_turismo ×8, PORTUGAL_NEWS ×1):**

| Chunk | Title | Source | Relevant? | Used? |
|---|---|---|---|---|
| 1 | Dois turistas brasileiros por minuto em Portugal | publico_turismo | ❌ | ❌ |
| 2 | Portugal faz campanha para turistas brasileiros | publico_turismo | ❌ | ❌ |
| 3 | Madeira e hotel lisboeta nos melhores Condé Nast UK | publico_turismo | ✅ | ✅ |
| 4 | Portugal for beginners | PORTUGAL_NEWS | ✅ | ❌ |
| 5 | Portugueses passam 18 dias no Brasil | publico_turismo | ❌ | ❌ |
| 6 | Hotéis portugueses favoritos Condé Nast Traveller | publico_turismo | ✅ | ❌ |
| 7 | Portugal está caro, portugueses fazem férias fora | publico_turismo | ❌ | ❌ |
| 8 | Polónia e Canadá puxam turistas estrangeiros | publico_turismo | ❌ | ❌ |
| 9 | Portugueses viajam na Páscoa | publico_turismo | ❌ | ❌ |
| 10 | Portugueses viajam mais no fim de ano | publico_turismo | ❌ | ❌ |

**Key findings:**
- **Retrieval failure** — 7/10 chunks are about Brazilian tourists in Portugal or Portuguese travel habits, not UK sentiment.
- **Missing expected sources** — GUARDIAN, TELEGRAPH, UK-specific media completely absent.
- **LLM missed Chunk #6** — Condé Nast Traveller hotels article had detailed UK reader votes (Savoy Palace, Yeatman, São Lourenço do Barrocal rankings) that would have enriched the answer.
- **Chunk #4 (Portugal for beginners)** from PORTUGAL_NEWS is a UK expat perspective, arguably relevant but not "what UK travelers are saying right now."
- **Answer very thin** — only 1 source cited, answer quality adequate but limited depth.
- **Worst retrieval precision in nochunk** — shows the config struggles with nationality-specific queries.

---

### Config 2: `small` (500 char / 100 overlap / 3-large)

| Q# | Rel. | Compl. | Prec. | Src Use | Ans Qual. | Total | Notes |
|---|---|---|---|---|---|---|---|
| 1 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 2 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 3 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 4 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 5 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 6 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 7 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 8 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 9 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 10 | /2 | /2 | /1 | /2 | /2 | /9 | |
| **Total** | | | | | | **/90** | |

---

### Config 3: `recursive` (2000 recursive / 200 overlap / 3-large)

| Q# | Rel. | Compl. | Prec. | Src Use | Ans Qual. | Total | Notes |
|---|---|---|---|---|---|---|---|
| 1 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 2 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 3 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 4 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 5 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 6 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 7 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 8 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 9 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 10 | /2 | /2 | /1 | /2 | /2 | /9 | |
| **Total** | | | | | | **/90** | |

---

### Config 4: `small-model` (2000 char / 200 overlap / 3-small)

| Q# | Rel. | Compl. | Prec. | Src Use | Ans Qual. | Total | Notes |
|---|---|---|---|---|---|---|---|
| 1 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 2 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 3 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 4 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 5 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 6 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 7 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 8 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 9 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 10 | /2 | /2 | /1 | /2 | /2 | /9 | |
| **Total** | | | | | | **/90** | |

---

### Config 5: `reduced-dims` (2000 char / 200 overlap / 3-large @ 1536d)

| Q# | Rel. | Compl. | Prec. | Src Use | Ans Qual. | Total | Notes |
|---|---|---|---|---|---|---|---|
| 1 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 2 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 3 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 4 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 5 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 6 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 7 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 8 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 9 | /2 | /2 | /1 | /2 | /2 | /9 | |
| 10 | /2 | /2 | /1 | /2 | /2 | /9 | |
| **Total** | | | | | | **/90** | |

---

## Summary Comparison

| Config | Retrieval (/50) | LLM (/40) | Total (/90) | Ranking | Key Observations |
|---|---|---|---|---|---|
| baseline | | | | | |
| nochunk | | | | | |
| small | | | | | |
| recursive | | | | | |
| small-model | | | | | |
| reduced-dims | | | | | |

---

## What Each Comparison Answers

| Comparison | Question Answered |
|---|---|
| baseline vs nochunk | Does chunking improve retrieval precision? |
| baseline vs small | Do smaller chunks give more precise results? |
| baseline vs recursive | Does smarter splitting improve quality over fixed-character? |
| baseline vs small-model | Is the cheaper embedding model "good enough"? |
| baseline vs reduced-dims | Can we compress the large model without losing quality? |
| small-model vs reduced-dims | Which is better: native small or compressed large? |

---

## Conclusions & Recommended Configuration

_To be filled after all tests are complete._

### Winner: `___________`

**Justification:**

1. 
2. 
3. 

### Trade-offs Considered
- Quality vs cost
- Build time vs retrieval accuracy  
- Storage size vs performance
