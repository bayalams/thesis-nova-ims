# Conde Nast Traveler Cleaning Overview

## 1. Source Identification
- **Source ID**: `CONDE_NAST_TRAVELER`
- **Base URL**: `cntraveler.com`

## 2. Issues Identified
1.  **Massive Privacy/GDPR Overlays**: Some articles contained a ~100-line "About Your Privacy" block with a list of 100+ vendors at the very start, pushing the actual header markers out of the search window.
2.  **Persistent Header Noise**: "Sign In", "Newsletters", and navigation menus appearing before the article body.
3.  **Markdown Image Links**: Large image links (`![Alt](URL)`) appearing in the middle of text or as lists.
4.  **UI Artifacts**: "Save to wishlist", "Chevron", "Arrow", and other usage cues.
5.  **Photo Credits**: Variations of "Photo: Name / Agency" or standalone agency names.

## 3. Cleaning Strategy (`clean_conde.py`)
- **Privacy Block Removal**: Implemented a robust regex to target the "About Your Privacy" block, using the reliable "EnglishDeutsch..." language selector string as the end marker. This ensures the massive vendor list is stripped before header detection.
- **Header Slicing**: Used a list of reliable end-markers (e.g., `Sign In`, `Newsletters`) to detect the end of the navigation header and slice the text from there.
- **Image Removal**: All Markdown images (`![...](...)`) are stripped to remove "massive links" and visual noise.
- **Persistent Noise Regex**: 
    - Generic "Name / Agency" photo credit removal.
    - Specific UI artifact removal ("Save to wishlist", "Chevron").
    - "Sign In" text removal (standalone and at start of text).

## 4. Verification
- **Sample Verified**: 5 documents, including the problematic file `27 Romantic Cabin Getaways` (ID: `4a98...`).
- **Result**: The cleaned text now starts immediately with the article content. Privacy blocks, navigation menus, and image links are successfully removed.
- **Status**: **READY** for ingestion.
