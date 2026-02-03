# El País Cleaning Overview

**Source ID:** `EL_PAIS_GENERAL`, `EL_PAIS_VIAJERO`, `EL_PAIS_ECONOMIA`, `EL_PAIS_ESPANA`
**Cleaner File:** `original_code/cleaners/clean_elpais.py`
**Dispatch Logic:** Matches "EL_PAIS" in source ID.

## Identified Noise Patterns

El País articles (across sub-brands) exhibit consistent and heavy noise patterns:

### Header Noise
- **Navigation Links:** "Ir al contenido", "Ir a los comentarios".
- **Social Shares:** "Compartir en Whatsapp", "Copiar enlace", etc.
- **Metadata Lines:**
    - "12 ENE 2026 - 06:30 CET" (Date usually duplicated in body)
    - "!Author Name" or "Author Name" lines.
- **Subscription Banners:** Occur at the top or inline.

### Footer Noise
- **Markers:**
    - "Más información" / "Archivado En" (Tags)
    - "Comentarios" links.
    - "Recomendaciones EL PAÍS" / "Lo más visto".
    - "Se adhiere a los criterios de..."
    - "Si está interesado en licenciar este contenido"

## Cleaning Strategy

1.  **Block Cut (Header):**
    - The cleaner aggressively looks for "Copiar enlace" or "Ir a los comentarios" within the first 3000 characters.
    - If found, it slices off **everything preceding** these markers. This effectively removes the messy "Ir al contenido ... Date ... Author" header block in one go, which is more robust than line-by-line regexes against variable formatting.

2.  **Fallback & Scrubbing:**
    - Explicit regex removal for "Ir al contenido", Date lines (Spanish/English formats), and Author lines.
    - **Artifact Removal**: Robust regex removal for block cut residues like `](#comments_container)`.
    - Removal of "Compartir en..." lines.

3.  **Footer Slicing:**
    - Slice text at the earliest occurrence of footer markers ("Más información", "Archivado En", "Comentarios").

4.  **Inline Cleaning:**
    - Removal of `Urgente [Location] - [Date]` prefixes in body text.
    - Flattening of markdown links `[Text](URL)` to `Text`.

## Metadata Handling
- **Structure**: Date, Title, and Tags are extracted to the metadata dictionary but **removed from the cleaned body text**.
- **Report Format**: Creating verified content for RAG requires the body to be free of metadata headers. This is strictly enforced.

## Verification Results

- **Reduction:** consistently high (70-90% noise reduction).
- **Quality:** Body text is clean, starting immediately with the content. No metadata headers are prepended to the text. Artifacts like `](#comments_container)` are verified removed.
