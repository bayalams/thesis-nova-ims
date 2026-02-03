# Cleaning Overview: HOSTELTUR

## 1. Source Analysis
- **Type**: Spanish B2B Travel News (professional/industry focus)
- **Structure**: Content in `scrapingbee.content`, dates in RFC format (`published` field)
- **Noise Profile**:
    - **Header**: Trending topics bar with `·` separated links
    - **Footer**: "Noticias relacionadas", "Los más leídos", Premium banners, cookie consent
    - **Inline**: Image markdown, `Fuente:` captions, "Hosteltur" signature

## 2. Cleaning Strategy (`clean_hosteltur.py`)
- **Freshness Filter**: 90-day cutoff using RFC date parsing
- **Tag Extraction**: Parses "Más sobre" section to populate `meta['tags']` before removal
- **Header Trimming**: Title-based (`trim_header_by_title`)
- **Footer Trimming**: Hard stop on "Noticias relacionadas", "Los más leídos", Premium banners
- **Post-Processing**:
    - Strip markdown links `[text](url)` → `text`
    - Remove image captions (`Fuente:...`)
    - Remove `###` markers and `Hosteltur` signature

## 3. Verification
- **Sample Size**: 20 articles (87 total)
- **Reduction**: 65-94%
- **Tags**: Successfully extracted from "Más sobre" section
- **Edge Case**: One article (Exceltur) scraped only nav content (scraping failure, not cleaning)

## 4. Next Steps
- Monitor for Premium paywall changes that might block scraping
