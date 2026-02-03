# Cleaning Overview: LE_FIGARO

## 1. Source Analysis
- **Type**: French News (GENERAL) & Travel (VOYAGES)
- **Structure**: Content in `scrapingbee.content`, dates in RFC format, tags in metadata
- **Noise Profile**:
    - **Header**: Nav ("Aller au contenu"), breadcrumbs, share links
    - **Footer**: "À lire aussi", "La rédaction vous conseille", cookie walls, paywall snippets
    - **Inline**: "Publicité", audio player markers, "Suivre", "Sujets"

## 2. Cleaning Strategy (`clean_le_figaro.py`)
- **Freshness Filter**: 90-day cutoff
- **Header Trimming**: Title-based
- **Footer Trimming**: Hard stop on "À lire aussi", comments, cookie walls
- **Skip Patterns**: Breadcrumbs, audio player, share buttons, time markers
- **Post-Processing**: Link stripping, heading underline removal

## 3. Verification
- **Sample Size**: 20 articles (81 total: 45 GENERAL + 36 VOYAGES)
- **Reduction**: 58-97%
- **Filtered**: 3 hotel articles (likely fully paywalled)
- **Note**: Some paywall snippets remain at end ("Cet article est réservé aux abonnés")

## 4. Known Limitations
- Paywall truncates some articles at ~15-30%
- Breadcrumbs may appear if title trimming doesn't catch them
