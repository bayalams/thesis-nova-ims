# RAG App Evaluation Log (Claude Opus 4.5)

**Purpose:** Document and evaluate the RAG system's performance from a tourism stakeholder perspective (e.g., Turismo de Portugal)

**Evaluation Date:** 2026-01-30

---

## Test 1: Emerging Travel Trends

### Query
> "What emerging travel trends are being discussed in international media that could affect Portugal's tourism strategy?"

### Answer (Generated)
Emerging travel trends that could affect Portugal's tourism strategy include a growing focus on sustainability and the balance between tourism growth and local community well-being. There is increasing awareness of overtourism, leading travelers to consider destinations that are less crowded and more sustainable. This sentiment is reflected in the discussions about how Portugal is experiencing a record influx of tourists, which, while beneficial for the economy, is causing strain on local infrastructure and affecting the quality of life for residents [Source 1].

Furthermore, the Portuguese government acknowledges the potential for tourism growth, but emphasizes the need to manage it sustainably. The tourism sector is projected to continue growing, with a focus on quality over quantity. This includes improving tourism revenue and diversifying the types of tourism offered, such as cultural experiences that engage with local communities [Source 2, 6]. There is also a push to attract high-value tourists from markets like the United States and Brazil, which underscores the importance of tailoring marketing strategies to attract a more affluent demographic [Source 3, 4].

Additionally, the potential impacts of infrastructure constraints, particularly in airports and other transport systems, are significant. There have been reports of long queues at airports, which could detract from the tourist experience [Source 8]. Addressing these challenges while promoting sustainability could be key components of Portugal's tourism strategy moving forward [Source 9].

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 7 |
| Precision | 70% |

### Sources Used
1. Far from the madding crowd (PORTUGAL_NEWS)
2. Tourism in Portugal continues to grow (PORTUGAL_NEWS)
3. No turismo "o crescimento será mais moderado..." (AMBITUR)
4. Portugal está caro e os portugueses fazem cada vez mais férias lá fora (Público)
6. No turismo "o crescimento será mais moderado..." (AMBITUR - chunk 1)
8. Queues at Faro airport cause concern (PORTUGAL_NEWS)
9. Estratégia turística 2035 para região Norte... (Público)

### Evaluation

**Result: ❌ FAILURE**

**Critical Issue:**
The query explicitly asked for **"international media"** perspectives, but **all 10 retrieved sources were Portuguese publications** (PORTUGAL_NEWS, AMBITUR, Público). The system completely failed to retrieve content from international sources like CNN Travel, Condé Nast Traveler, Guardian Travel, BBC, etc.

**What went wrong:**
- Semantic search prioritized content *about* Portugal tourism trends rather than content *from international sources* about Portugal
- The system lacks source-type filtering or the ability to distinguish source origin
- The answer is factually accurate but **does not answer the actual question asked**

**Minor positives (insufficient to pass):**
- Answer structure and coherence were good
- Sources were recent (2024-2026)

**Rating:** ⭐ (1/5) - Failed to address the core requirement of the query

**Root Cause Hypothesis:**
The embedding similarity matched on "Portugal" + "tourism" + "trends" but ignored the "international media" constraint. This suggests the need for:
1. Better query understanding / keyword filtering
2. Source metadata filtering capability
3. Or reformulating queries to be more explicit

### Suggested Follow-up Questions
1. "What are international travel publications saying about Portugal as a destination for 2026?"
2. "What negative issues or concerns about visiting Portugal are being reported in international media?"
3. "How does Portugal compare to competing destinations like Spain, Greece, or Croatia in travel media coverage?"

---

## Test 2: International Travel Publications on Portugal 2026

### Query
> "What are international travel publications saying about Portugal as a destination for 2026?"

### Answer (Generated)
Portugal is emerging as a noteworthy destination for international travelers in 2026, as highlighted by various travel publications and analyses. According to a report by TripAdvisor, Madeira has been recognized as the top trending destination worldwide for 2026, appealing to those seeking adventure amidst stunning natural landscapes [Source 9]. This recognition underscores the island's growing popularity and its appeal as a premier travel location.

Additionally, tourism in Portugal is projected to continue its robust growth trajectory. The country witnessed a record influx of 33 million visitors in 2025, with expectations for similar success in 2026, albeit with a more moderated growth rate [Source 2, 10]. The Secretary of State for Tourism indicated that the sector should see consistent growth of about 2.5% in 2026, with revenues expected to increase by 5-7% [Source 6].

Despite the positive outlook, concerns about overtourism in key areas such as Lisbon and Porto have been raised. These cities have experienced overwhelming tourist numbers, leading to increased pressure on local infrastructure and housing [Source 2, 3, 10]. This situation calls for a shift towards more sustainable tourism practices that benefit both visitors and local communities [Source 3].

Moreover, Portugal's real estate market remains attractive to international investors, driven by the country's political stability, legal predictability, and integration into the eurozone, which enhance its appeal for tourism-related investments [Source 1, 4]. 

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 7 |
| Precision | 70% |

### Source Breakdown
| Source | Type | Used? |
|--------|------|-------|
| PORTUGAL_NEWS | Portuguese | ✓ (x5) |
| PORTUGAL_RESIDENT | Portuguese | ✓ |
| AMBITUR | Portuguese | ✓ |
| **EURONEWS_TRAVEL** | **International** | ✓ |

**International sources: 1/10 (10%)**

### Evaluation

**Result: ⚠️ PARTIAL SUCCESS**

**Improvement over Test 1:**
- This time, 1 international source was retrieved: **Euronews Travel** (Source 9)
- The Euronews chunk contained valuable international perspective (TripAdvisor Travellers' Choice Awards, Madeira as #1 trending destination)

**Still problematic:**
- 9 out of 10 sources are still Portuguese publications
- The answer claims to be about "international travel publications" but mostly cites domestic sources
- Missing: CNN Travel, Condé Nast Traveler, Guardian Travel, BBC Travel, Travel + Leisure, etc.

**Positive aspects:**
- Answer is well-structured and informative
- Correctly identifies key trends: Madeira recognition, overtourism concerns, growth projections
- The ONE international source (Euronews) was actually used effectively

**Rating:** ⭐⭐ (2/5) - Marginal improvement, found 1 international source but still dominated by Portuguese media

### Key Insight
The query refinement ("international travel publications" vs "international media") did marginally improve results, suggesting the system responds somewhat to query specificity. However, it still struggles to prioritize sources by origin.


---

## Test 3: Explicit Source Naming (CNN, Condé Nast, Guardian)

### Query
> "According to CNN Travel, Condé Nast Traveler, and The Guardian, what are the top reasons to visit Portugal in 2026?"

### Answer (Generated)
Portugal is expected to be a highly attractive destination in 2026 for several compelling reasons:

1. **Diverse Natural Landscapes**: Portugal offers stunning natural beauty, including the rugged cliffs and beaches of the Algarve, the lush mountains of Madeira, and the unique landscapes of the Azores. Madeira, in particular, has gained recognition as a leading adventure destination in Europe [Source 3].

2. **Cultural Richness**: Portugal boasts a rich cultural heritage with historic cities like Lisbon and Porto. The country attracts travelers interested in gastronomy, particularly its renowned wines [Source 10].

3. **Recognition in Travel Awards**: Portugal has been acknowledged in various travel awards, including "World's Leading Beach Destination" for the Algarve and Madeira ranked #1 trending destination by Tripadvisor [Source 2, 3, 6].

4. **Growing Tourism Infrastructure**: Tourism contributes over 20% to GDP and continues to attract investment [Source 1, 9].

5. **Sustainable Tourism Development**: Growing emphasis on sensitive tourism that respects local cultures [Source 2, 9].

6. **Appeal of Urban Centers**: Cities like Lisbon are vibrant hubs, though there are conversations about managing over-tourism [Source 1, 2].

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 6 |
| Precision | 60% |

### Source Breakdown - Did it find the requested publications?

| Requested | Found? | Notes |
|-----------|--------|-------|
| **CNN Travel** | ❌ NO | Not a single CNN Travel article retrieved |
| **Condé Nast Traveler** | ⚠️ INDIRECT | Found via Público article *reporting on* CNT awards (Source 6) |
| **The Guardian** | ❌ NO | Not a single Guardian article retrieved |

**Actual sources retrieved:**
| Source | Type | Count |
|--------|------|-------|
| PORTUGAL_NEWS | Portuguese | 5 |
| PORTUGAL_RESIDENT | Portuguese | 1 |
| publico_turismo | Portuguese | 2 |
| EURONEWS_TRAVEL | International | 1 |
| CNN_TRAVEL | International | 0 |
| GUARDIAN_TRAVEL | International | 0 |

### Evaluation

**Result: ❌ FAILURE**

**Critical Issue:**
The query **explicitly named 3 specific publications** (CNN Travel, Condé Nast, Guardian), but the system:
- Found **0 direct articles** from any of them
- Found Condé Nast **indirectly** via a Público article reporting on their awards
- Did not acknowledge that it couldn't find content from the requested sources

**What went wrong:**
1. Semantic search matched on "Portugal" + "reasons to visit" + "2026" but **completely ignored the source constraints**
2. The LLM answered as if it had the requested sources, when it didn't
3. This is a **hallucination of authority** - the answer implies sources it doesn't have

**Are these sources even in the corpus?**
This raises the question: Does the database actually contain CNN Travel, Condé Nast, or Guardian articles? If not, the system should acknowledge this limitation.

**Rating:** ⭐ (1/5) - Failed to retrieve from explicitly named sources; LLM didn't disclose this limitation

### Key Insight
Explicitly naming sources in the query does NOT help retrieval. The embedding similarity still matches on topical content, not source metadata. This confirms the need for:
1. **Metadata filtering** (filter by source before semantic search)
2. **Honest acknowledgment** when requested sources aren't found


---

## Test 4: Threat Detection (No Source Constraint)

### Query
> "What negative issues, problems, or concerns about Portugal as a tourist destination have been reported recently?"

### Answer (Generated)
Recent reports have highlighted several negative issues and concerns regarding Portugal as a tourist destination:

1. **Overtourism and Local Impact**: Growing concerns about overtourism, particularly in Lisbon. Locals are avoiding popular neighborhoods like Alfama due to the overwhelming presence of tourists [Source 1].

2. **Airport Congestion**: Significant delays and long queues at airports, particularly Faro and Lisbon. Passengers have faced waits of over four hours at Lisbon airport [Source 2, Source 10].

3. **Infrastructure Strain**: Rapid tourism growth has put pressure on infrastructure, public spaces, and resources [Source 1, Source 3].

4. **Economic Disparities**: A considerable portion of the population lives in poverty or social exclusion, contrasting with the thriving tourism industry [Source 9].

5. **Housing Crisis**: The tourism boom has exacerbated the housing crisis, with properties converted to short-term rentals causing a shortage of affordable housing [Source 8].

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 6 |
| Chunk Usage | 60% |

### Source Breakdown
| Source | Type | Count |
|--------|------|-------|
| PORTUGAL_NEWS | Portuguese | 7 |
| publico_turismo | Portuguese | 3 |

### Evaluation

**Result: ✅ SUCCESS**

**Why this worked:**
- No source constraints were specified in the query
- The query asked for *topical* content (negative issues) which semantic search handles well
- The system correctly identified 5 distinct threat categories

**Answer Quality:**
- ✅ Comprehensive - covered overtourism, airports, infrastructure, economy, housing
- ✅ Specific - cited concrete examples (4+ hour waits, Alfama neighborhood)
- ✅ Well-structured - organized by issue category
- ✅ Properly cited - each claim backed by source references

**Rating:** ⭐⭐⭐⭐⭐ (5/5) - Excellent threat detection when no source constraints applied

### Key Insight
The system performs well on **topical queries without source constraints**. This is its strength - semantic similarity matching on content topics.

---

## Test 5: Competitor Analysis (Spain, Greece, Croatia)

### Query
> "How is Portugal positioned compared to Spain, Greece, or Croatia as a tourism destination?"

### Answer (Generated)
Portugal is increasingly recognized as a significant tourism destination in Europe, ranking fifth in the European Union for revenues generated by foreign tourists. In 2024, it generated approximately €28 billion in tourism revenue, surpassing Greece and positioning itself favorably compared to Spain, which leads with €98 billion [Source 3].

Portugal benefits from a diverse range of tourists, with American visitors becoming a significant market, surpassing even Spain in 2024 [Source 3]. While Portugal enjoys strong tourism growth, it faces challenges similar to Spain and Croatia regarding overtourism [Source 1, 10].

Portugal's positioning is strong, particularly in terms of revenue generation and appeal to digital nomads, making it competitive alongside Spain, Greece, and Croatia [Source 4, 10].

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 5 |
| Chunk Usage | 50% |

### Source Breakdown
| Source | Type | Count |
|--------|------|-------|
| PORTUGAL_NEWS | Portuguese | 6 |
| PORTUGAL_RESIDENT | Portuguese | 1 |
| publico_turismo | Portuguese | 2 |
| **RTP_NOTICIAS** | Portuguese (public broadcaster) | 1 |

### Evaluation

**Result: ⚠️ PARTIAL SUCCESS**

**What worked:**
- Found concrete comparative data: Portugal 5th in EU, €28B vs Spain's €98B
- Identified Portugal's rising appeal to American tourists
- Mentioned digital nomad positioning (ranked above Spain)

**What's missing:**
- No actual articles **about** Spain, Greece, or Croatia - only Portuguese sources mentioning them
- Comparison is one-directional (Portugal vs others), not bi-directional
- Claims like "challenges similar to Spain and Croatia" are inferential, not from dedicated competitor analysis
- No insight into what competitors are doing differently

**Rating:** ⭐⭐⭐ (3/5) - Provides ranking context but lacks true competitive intelligence

### Key Insight
The system can surface **Portugal's position relative to competitors** when Portuguese media reports on rankings. However, it cannot provide **actual competitor intelligence** (what competitors are doing, their strategies, their challenges) because the corpus appears to be Portugal-focused.

---

## Test 6: Competitor Alternatives Query

### Query
> "What competing destinations are being promoted as alternatives to Portugal in travel media?"

### Answer (Generated)
The provided sources do not explicitly mention specific competing destinations being promoted as alternatives to Portugal in travel media. Most of the information focuses on Portugal's tourism success, its appeal, and accolades, such as being recognized as the best destination in Europe and having Madeira named the best island in Europe [Source 4, 6].

Since the sources do not provide adequate information on competing destinations, I cannot offer a list of alternatives to Portugal as highlighted in travel media.

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 6 |
| Chunk Usage | 60% |

### Source Breakdown
| Source | Type | Count |
|--------|------|-------|
| PORTUGAL_NEWS | Portuguese | 4 |
| publico_turismo | Portuguese | 5 |
| EURONEWS_TRAVEL | International | 1 |

### Evaluation

**Result: ⚠️ RETRIEVAL MISS (Query-Content Semantic Gap)**

**What went RIGHT:**
- ✅ The LLM **acknowledged it couldn't answer** the question
- ✅ No hallucination - didn't make up competitor destinations
- ✅ Honest about limitations

**What went WRONG - Retrieval Failure:**
The corpus **DOES contain** competitor information, but it wasn't retrieved because the query framing didn't match how competitors are discussed in articles.

**Example of missed content:**
- **Article:** "The Most Romantic Hotels in the Entire World" (Condé Nast Traveler)
- **Source:** `CONDE_NAST_TRAVELER` - exists in corpus but NOT retrieved
- **Content:** Lists hotels in Greece, Italy, Spain, Croatia, France, Austria, Ireland, Iceland... with only 1 Portugal property (Six Senses Douro Valley)
- **Why missed:** Query asked for "alternatives to Portugal" but article discusses "romantic destinations worldwide"

**Other likely missed content:**
- "Trending destinations 2026" articles listing Spain, Greece, Croatia
- "Digital nomad rankings" mentioning Portugal vs Spain, Hungary, Romania
- "Best islands in Europe" comparing Madeira to Greek islands

**The core problem:**
| Query Framing | Article Framing |
|---------------|-----------------|
| "alternatives to Portugal" | "best hotels in the world" |
| "competing destinations" | "top destinations 2026" |
| "promoted as alternatives" | implicit competition through rankings |

The semantic embeddings of the query don't match the embeddings of articles that *contain* the answer but *frame it differently*.

**Comparison to Test 3:**
| Behavior | Test 3 | Test 6 |
|----------|--------|--------|
| Had relevant sources in corpus? | Unclear | **YES** |
| Retrieved them? | No | **No** |
| Acknowledged gap? | ❌ No | ✅ Yes |
| Hallucinated answer? | ⚠️ Partial | ❌ No |

**Rating:** ⭐⭐⭐ (3/5) - LLM was honest, but retrieval failed to find existing content

### Key Insight
**Query-content semantic gap:** The information exists but is framed differently than the query. This suggests:
1. Users need to phrase queries closer to how content is actually written
2. The system could benefit from query expansion or reformulation
3. Multi-hop retrieval might help (first find "destination rankings", then extract competitors)
---

## Test 7: Query Reformulation (A/B Comparison to Test 6)

### Query
> "What touristic destinations are trending?"

### Answer (Generated)
Trending tourist destinations for 2026 include a mix of popular cultural events and emerging hotspots. Notably, Rio de Janeiro is experiencing a surge in tourism due to its famous Carnival. In addition, cities like Milan are attracting visitors in anticipation of the 2026 Winter Olympics.

For solo travelers, the Algarve region in Portugal is highlighted as a top destination, alongside other European locations such as Costa del Sol in Spain and Isère in France. Culinary travel is also on the rise, with Lisbon becoming a hotspot for food experiences.

Other trending destinations include Madeira, Portugal; Jaipur, India; Bodrum, Turkey; Crete, Greece; and Sardinia, Italy.

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 5 |
| Chunk Usage | 50% |

### Source Breakdown
| Source | Type | Count |
|--------|------|-------|
| TRAVEL_LEISURE | International | 3 |
| CNBC_TRAVEL | International | 2 |
| SKIFT | International | 2 |
| CONDE_NAST_TRAVELER | International | 1 |
| TOURISTIK_AKTUELL | International (DE) | 1 |

### Evaluation

**Result: ✅ SUCCESS - Query Reformulation Works**

**Comparison to Test 6:**
| Aspect | Test 6 | Test 7 |
|--------|--------|--------|
| Query | "What competing destinations are being promoted as alternatives to Portugal?" | "What touristic destinations are trending?" |
| Intent | Find competitors | Find competitors (implicit) |
| Intl Sources Found | 1 (10%) | 9 (90%) |
| Competitors Listed | 0 | 10+ countries |
| Result | ❌ MISS | ✅ SUCCESS |

**Competitors now found:**
- 🇪🇸 Spain (Costa del Sol)
- 🇫🇷 France (Isère, Paris)
- 🇬🇷 Greece (Crete)
- 🇮🇹 Italy (Sardinia, Milan)
- 🇮🇳 India (Jaipur, Bangalore)
- 🇹🇷 Turkey (Bodrum)
- 🇲🇦 Morocco (Marrakesh)
- 🇯🇵 Japan (Tokyo, Nakano)
- 🇧🇷 Brazil (Rio, João Pessoa)
- 🇨🇷 Costa Rica (Limón)

**Why it worked:**
The query "trending destinations" semantically matches article framing:
- "2026 Travel Trends" articles
- "Trending destinations" lists
- "Top places to visit" content

**Rating:** ⭐⭐⭐⭐⭐ (5/5) - Same corpus, better query = excellent results

### Key Insight
**Query formulation is critical for RAG success.** Users should phrase queries to match how content is typically written in source documents, not how they conceptually think about the question.

| User Thinking | Article Framing | Match? |
|---------------|-----------------|--------|
| "Alternatives to Portugal" | N/A | ❌ No |
| "Trending destinations" | "2026 travel trends" | ✅ Yes |
| "Best places to visit" | "Top destinations" | ✅ Yes |

---

## Test 8: Multi-Dimensional Query (Budget + Age Segments)

### Query
> "What touristic destinations are trending for each economic segment, from low budget to luxury, as well as age segments?"

### Answer (Generated)
**Low-budget travelers**: Secondary cities and off-peak travel. Avoiding heavily visited destinations to connect more authentically with local cultures and save money. 15% faster growth in Asia's secondary destinations.

**Mid-range travelers**: Personalized escapades aligned with hobbies, literature, or popular media. Budget-conscious but seeking meaningful experiences.

**Luxury travelers**: "Hushpitality" - less stimulation, more tranquility. Decision-light travel, curated choices that reduce cognitive overload.

**Seniors (50+)**: Driving desegmentation as they're less tied to traditional peak seasons.

**Under 35**: Active and wellness-focused trips, viewing travel as long-term health investment.

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 5 |
| Chunk Usage | 50% |

### Source Breakdown
| Source | Type | Count |
|--------|------|-------|
| CNBC_TRAVEL | International | 2 |
| SKIFT | International | 4 |
| EL_PAIS_VIAJERO | International (ES) | 1 |

### Evaluation

**Result: ✅ SUCCESS - Complex Multi-Faceted Query Handled Well**

**What went RIGHT:**
- ✅ Retrieved **diverse international sources** (CNBC, Skift, El País)
- ✅ **Segmented answer** by budget level AND age group
- ✅ Industry-specific terminology ("hushpitality", "decision-light travel")
- ✅ Concrete data points (15% growth in secondary destinations)
- ✅ Spanish-language source (El País Viajero) retrieved and synthesized

**Segmentation quality:**
| Segment | Covered? | Insight Quality |
|---------|----------|-----------------|
| Low budget | ✅ | Good - secondary cities, off-peak |
| Mid-range | ✅ | Good - personalized escapades |
| Luxury | ✅ | Excellent - "hushpitality" trend |
| Seniors | ✅ | Good - desegmentation driver |
| Youth (<35) | ✅ | Good - wellness focus |

**Rating:** ⭐⭐⭐⭐⭐ (5/5) - Excellent handling of complex multi-dimensional query

### Key Insight
The system handles **complex, multi-faceted queries** well when:
1. The query uses industry terminology ("economic segment", "budget", "luxury")
2. The content is framed similarly in articles (trend reports naturally segment by traveler type)
3. No source constraints are imposed

---

---

## Test 9: Competitive Intelligence - Spain vs Portugal Marketing

### Query
> "What is Spain doing differently in tourism marketing compared to Portugal?"

### Answer (Generated)
Spain is implementing several distinctive strategies in tourism marketing:

1. **Diversification of Destinations**: Spain is actively promoting its interior regions to reduce pressure on coastal areas, encouraging visitors to explore lesser-known attractions.

2. **Ecotourism Initiatives**: Spain is developing Europe's largest ecotourism corridor - "Corredor Ecoturístico España Verde" - connecting Galicia, Asturias, Cantabria, and Basque Country.

3. **Focus on Cultural and Gastronomic Experiences**: The "España Verde" brand emphasizes sophisticated wine and gastronomy offerings, with partnerships with renowned chefs.

4. **Targeting Portuguese Tourists**: Spain is positioning itself as an attractive destination for Portuguese tourists, with campaigns tailored specifically for this demographic.

5. **International Marketing Campaigns**: Spain participates in fairs like FITUR to strengthen ties with other countries and enhance cross-border tourism.

In contrast, Portugal's strategy focuses more on consolidating existing markets and enhancing quality rather than diversifying offerings significantly.

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 7 |
| Chunk Usage | 70% |

### Source Breakdown
| Source | Type | Count | Used |
|--------|------|-------|------|
| publico_turismo | Portuguese | 4 | 3 |
| AMBITUR | Portuguese Trade | 4 | 2 |
| PORTUGAL_NEWS | Portuguese (EN) | 1 | 1 |
| *Spanish sources* | - | 0 | - |

### Evaluation

**Result: ✅ SUCCESS - Strong Competitive Intelligence**

**What worked well:**
- Retrieved relevant information about Spain's "España Verde" initiative
- Found specific details: ecotourism corridor, 56 Michelin restaurants, 42 protected areas
- Provided genuine comparative analysis
- Well-structured answer with 5 distinct strategic differences
- High chunk usage (70%)

**Limitation noted:**
All sources are Portuguese publications reporting ON Spain (from FITUR coverage), not Spanish sources reporting their own strategy. For deeper competitive intelligence, Spanish sources like El País, Hosteltur, or Spain's tourism ministry would provide more direct insight.

**Rating:** ⭐⭐⭐⭐ (4/5) - Excellent comparative answer, minor source perspective gap

### Key Insight
The corpus effectively captures **competitor information through trade event coverage** (FITUR). Portuguese industry publications report on Spanish initiatives when both countries participate in the same events. This is a valid intelligence pathway.

---

## Test 10: Algarve Competitive Positioning

### Query
> "How is the Algarve positioned against competing Mediterranean destinations?"

### Answer (Generated)
The Algarve is well positioned against competing Mediterranean destinations, as evidenced by its recognition as "Best Summer Destination" at the 2026 Irish Travel Industry Awards (fifth time winning). This reflects strong appeal to Irish tourists (75% of overnight stays in 2024, third most important foreign market).

Competitors mentioned: Costa del Sol, Greece, Lanzarote, Spain.

The Algarve's strategy emphasizes air accessibility, quality experiences, and safety.

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 4 |
| Chunk Usage | 40% |

### Source Breakdown
| Source | Type | Count | Used |
|--------|------|-------|------|
| PORTUGAL_NEWS | Portuguese (EN) | 2 | 2 |
| PORTUGAL_RESIDENT | Portuguese (EN) | 2 | 1 |
| AMBITUR | Portuguese Trade | 6 | 1 |

### Evaluation

**Result: ⚠️ PARTIAL - Narrow Answer**

**What the answer provides:**
- ✅ Irish Travel Industry Award wins (5 times)
- ✅ Irish market share data (75% of overnight stays)
- ✅ Lists competitors: Costa del Sol, Greece, Lanzarote, Spain

**What the answer lacks:**
- ❌ No actual competitive analysis (what makes Algarve different?)
- ❌ No comparison of prices, experiences, or offerings
- ❌ No intelligence on what competitors are doing
- ❌ Heavy focus on ONE market (Ireland) - what about UK, Germany, France?
- ❌ No discussion of threats or weaknesses

**The answer essentially says:** "Algarve won an Irish award, therefore it's well-positioned" - but this isn't true competitive intelligence.

**Rating:** ⭐⭐⭐ (3/5) - Found relevant award data but missed the deeper competitive analysis the question implied

### Key Insight
**Corpus gap:** The database contains recognition/award news but lacks comparative market analysis articles that would discuss WHY travelers choose Algarve vs Costa del Sol, pricing differences, or competitor strategies. For true competitive positioning, the corpus needs strategic analysis content, not just press releases.

---

## Summary Statistics

---

## Test 11: UK Traveler Sentiment

### Query
> "What are UK travelers saying about Portugal right now?"

### Answer (Generated)
UK travelers are currently expressing a strong interest in Portugal. British tourists accounted for 13.8% of overnight stays, despite a slight decrease. UK citizens spent around £2.2 billion in Portugal. The tourism sector is projected to grow at 5% annually.

### Retrieval Metrics
| Metric | Value |
|--------|-------|
| Chunks Retrieved | 10 |
| Chunks Used | 3 |
| Chunk Usage | 30% |

### Source Breakdown
| Source | Type | Count | Used |
|--------|------|-------|------|
| PORTUGAL_NEWS | Portuguese (EN) | 5 | 3 |
| publico_turismo | Portuguese | 4 | 0 |
| *UK sources* | - | 0 | - |

### Evaluation

**Result: ❌ FAIL - Wrong Question Answered**

**The question asked:** What are UK travelers **SAYING** (sentiment, opinions, feedback)

**The answer provided:** UK traveler **STATISTICS** (overnight stays, spending)

| Asked For | Got |
|-----------|-----|
| Opinions | Statistics |
| Sentiment | Market share data |
| Reviews/feedback | Spending figures |
| What UK media reports | Portuguese data about UK tourists |

**Critical issues:**
- ❌ Zero UK sources (no Guardian, Telegraph, BBC Travel, etc.)
- ❌ No actual traveler sentiment or quotes
- ❌ No mention of what UK travelers like/dislike about Portugal
- ❌ Answer conflates "strong interest" with market statistics
- ❌ Lowest chunk usage yet (30%)

**Rating:** ⭐⭐ (2/5) - Answered a different question entirely

### Key Insight
**Corpus gap + Question interpretation failure:**
1. The corpus lacks UK media content about Portugal experiences
2. The LLM interpreted "saying" as "demonstrating via statistics" rather than "expressing opinions"

For this type of query, the system needs:
- UK travel publication articles (The Telegraph Travel, Guardian Travel)
- Review aggregation content
- Social media sentiment analysis
- UK traveler experience stories

---

| Test | Query Topic | Chunk Usage | Source Accuracy | Rating | Notes |
|------|-------------|-------------|-----------------|--------|-------|
| 1 | Emerging trends (intl media) | 70% | 0% (0/10 intl) | ⭐ (FAIL) | Asked for international media, got only Portuguese |
| 2 | Intl travel publications | 70% | 10% (1/10 intl) | ⭐⭐ (PARTIAL) | Found 1 intl source (Euronews) |
| 3 | Explicit sources (CNN/CNT/Guardian) | 60% | 0% (0/3 found) | ⭐ (FAIL) | Named 3 sources, found 0 directly |
| 4 | Threat detection (no constraint) | 60% | N/A | ⭐⭐⭐⭐⭐ (PASS) | Excellent topical retrieval, 5 issues identified |
| 5 | Competitor analysis | 50% | N/A | ⭐⭐⭐ (PARTIAL) | Found rankings but no true competitor intel |
| 6 | Competitor alternatives | 60% | N/A | ⭐⭐⭐ (MISS) | Retrieval missed existing content due to query-framing gap |
| 7 | Trending destinations | 50% | 90% (9/10 intl) | ⭐⭐⭐⭐⭐ (PASS) | Query reformulation = success |
| 8 | Budget + age segments | 50% | 100% (7/7 intl) | ⭐⭐⭐⭐⭐ (PASS) | Excellent multi-dimensional response |
| 9 | Spain vs Portugal marketing | 70% | N/A | ⭐⭐⭐⭐ (PASS) | Strong competitive intel via trade event coverage |
| 10 | Algarve vs Mediterranean | 40% | N/A | ⭐⭐⭐ (PARTIAL) | Found awards but lacked true competitive analysis |
| 11 | UK traveler sentiment | 30% | 0% (0/10 UK) | ⭐⭐ (FAIL) | Gave statistics instead of sentiment/opinions |

---

## Overall Observations

**Semantic search limitations**: Semantic search alone can't handle source-type constraints. The system would need either:  
- Hybrid search (semantic + metadata filtering)
- Better prompt engineering (e.g., "from CNN, BBC, Guardian...")
- Or a two-stage retrieval approach

**Source authority concern (for future consideration):**  
The generator relies heavily on **The Portugal News** and **The Portugal Resident**. While these sources are relevant for Portugal-focused content, they are niche expat publications with limited international reach. 

For a tourism stakeholder like Turismo de Portugal, sources like **Condé Nast Traveler**, **El País**, **The Guardian**, **CNN Travel**, or other well-known international outlets carry significantly more weight because:
- They shape international traveler perceptions
- They have wider readership in key source markets (UK, US, Spain, Germany)
- Their coverage signals how Portugal is being positioned globally

This imbalance should be considered when evaluating the system's usefulness for strategic intelligence.

---

## Data Quality Issue: Skift Cleaner Noise

**Problem identified during Test 8:**
Skift chunks retrieved contain significant noise despite cleaning. Examples:

```
First read is on us.
Subscribe to read more essential travel industry news.
New users get 20% off their first year of Skift Pro
[Subscribe]...
Please ensure Javascript is enabled...
```

**Root cause analysis:**
1. The embedder uses the `text` field (cleaned content) ✅
2. The Skift cleaner (`clean_skift.py`) IS running ✅
3. BUT the cleaner doesn't fully remove:
   - Subscription CTAs repeated in article body
   - Podcast player UI elements
   - "Up Next" / "Related Articles" sections
   - Social media sharing prompts

**Impact on RAG:**
- Noisy chunks dilute retrieval quality
- LLM may cite promotional content as if it were article content
- Chunk precision drops when 20-30% of chunk is boilerplate


