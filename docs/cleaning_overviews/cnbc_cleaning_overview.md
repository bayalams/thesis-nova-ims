# CNBC_TRAVEL Cleaning Overview

## Source Characteristics
- **Source ID**: `CNBC_TRAVEL`
- **Content Format**: JSON `scrapingbee.content` (Markdown).
- **Structure**:
  - **Header**: Navigation links (`Skip Navigation`, `Markets`, `Menu`) and `Key Points` summary.
  - **Body**: Standard Markdown.
  - **Inline Noise**: `Stock Chart Icon`, `Zoom In Icon`, `Arrows pointing outwards`, `Getty Images` captions (isolated).
  - **Footer**: `This site is now part of Versant`, `Cookie Notice`, `Subscribe to CNBC`.

## Cleaning Strategy (`clean_cnbc.py`)

1.  **Header Cleaning**:
    - **Key Points**: Preserves "Key Points" and everything after, removing preceding navigation.
    - **Noise Filter**: Removes specific header noise lines (`Menu`, `watch now`, `PRO`, `Livestream`, `Skip Navigation`, etc.) if they appear at the start.
    - **Pattern Matching**: Removes `VIDEO\d:\d\d` timestamps.

2.  **Footer Cleaning**:
    - Truncates text at specific markers:
        - `This site is now part of`
        - `Cookie Notice`
        - `Subscribe to CNBC`
        - `Sign up for free`
        - `Recommended Video`
        - `Fed Notes`

3.  **Inline Cleaning**:
    - **Images**: Removes `![...](...)`.
    - **Specific Artifacts**:
        - `Zoom In Icon`
        - `Stock Chart Icon`
        - `Arrows pointing outwards`
        - `Getty Images` (isolated lines)
        - `Money Movers` (Program name)
    - **Separators**: Removes `---` or similar lines.
    - **Whitespace**: Collapses multiple newlines.

## Verification
- Verified against 5 samples.
- **File 1 (b555db...)**: Correctly identified as a "Cookie Wall" page with no content -> Output empty.
- **Files 2-5**: Clean content, extracted "Key Points", removed navigation and footer legalese.
