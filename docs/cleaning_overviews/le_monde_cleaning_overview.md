# Cleaning Overview: LE_MONDE

## 1. Source Analysis
- **Type**: French News (general, international, politics)
- **Structure**: Content in `scrapingbee.content`, dates in RFC format, no tags
- **Noise Profile**:
    - **Header**: Cookie consent, "Vous n'êtes pas inscrit"
    - **Footer**: Subscription prompts, games section, multi-device warnings
    - **Inline**: "Lire plus tard", archive links, photo credits

## 2. Cleaning Strategy (`clean_le_monde.py`)
- **Freshness Filter**: 90-day cutoff
- **Header Trimming**: Title-based
- **Footer Trimming**: Hard stop on subscription prompts, games, cookie walls
- **Post-Processing**: Link stripping, photo credit removal

## 3. Verification
- **Sample Size**: 20 articles (37 total)
- **Reduction**: 46-96%
- **Content Yield**: 1,500-5,000+ characters per article
- **Paywall Note**: Most articles truncated at ~20-30%, but still yield usable content
- **Full Content**: Live blogs ("EN DIRECT") have complete content

## 4. Decision
**KEEP** - Sufficient content for RAG despite paywall truncation.
