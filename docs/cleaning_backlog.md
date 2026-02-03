# Cleaning Noise Backlog

Documenting reported noise issues in cleaner modules for future resolution.

## Status Overview
- **BBC**: Partially fixed (regex updated), but needs broader verification.
- **El País**: Footer noise identified ("Tiene algo que contar", "Recomendaciones"). Regex updated but verification interrupted.
- **General**: Need to verify if `scripts/fix_noisy_articles.py` was successfully run or needs to be re-run.

## Reported Issues

### 1. BBC - Trailing Noise & Link Blocks
- **Example File**: `data/articles/42da9046792373792db3574a5d45a7898ac3c3f31ace2cf295eab8b933f2b793.json`
- **Link**: [Original Article](https://www.bbc.com/news/articles/c75xdg2p36lo?at_medium=RSS&at_campaign=rss)
- **Problem**: 
    - "More from the BBC" footer sections.
    - "Follow live updates" blocks leaving artifacts like `[`.
    - Trailing brackets from incomplete markdown link removal.
- **Current Status**: 
    - Regex added to `clean_bbc.py` to handle "More from..." and multiline blocks.
    - Added removal for stray `[` lines.

### 2. El País - Footer Ads & Contact Info
- **Example File**: `data/articles/0a745b2926b24eaadac942b7ff3655df42ce8aca26d56a14bec4c38ac83fd113.json`
- **Link**: [Original Article](https://elpais.com/espana/madrid/2026-01-12/la-familia-cazon-lista-para-colonizar-un-nuevo-barrio-de-madrid-mas-grande-que-zamora.html)
- **Problem**: 
    - "Recomendaciones EL PAÍS" section.
    - "***¿Tiene algo que contar?***" contact block at the end.
    - "Si está interesado en licenciar..." legal text.
- **Current Status**:
    - Added markers to `clean_elpais.py`.

## Action Plan (When Resuming)
1. **Verify Fixes**: Run `scripts/test_cleaners_debug.py` to confirm the latest regex changes eliminate the noise in the raw content of the example files.
2. **Apply Fixes**: Run `scripts/fix_noisy_articles.py` to update the actual JSON files.
3. **Broaden check**: Briefly scan other files from the same sources to ensure no regressions.
