# EI Mundo Cleaning Overview

**Source ID**: `EL_MUNDO`
**Cleaner**: `original_code/cleaners/clean_elmundo.py`
**Verification**: `project_documentation/elmundo_verification.md`

## Identified Noise
1.  **Massive Header Navigation**: El Mundo articles often start with a large list of links ("Es noticia", "Menú", "Últimas noticias").
2.  **Bylines & Dates**: "Actualizado Lunes, 12 enero..." appears right before the body.
3.  **Related News Bullets**: Debris at the start of the body, e.g., `* [Category] [Title]`.
4.  **Inline Noise**: "Audio generado automáticamente con IA", "Compartir en Facebook", internal markdown links like `[Text](private_url)`.
5.  **Footer**: "Ver enlaces de interés", "Comentarios", "Cargando siguiente contenido".

## Cleaning Strategy
1.  **Title Trim**: Standard `trim_header_by_title`.
2.  **Headline/Byline Slice**:
    - Locates the "Actualizado <Date>" pattern (regex) to cut everything before the body content.
    - If that fails, falls back to the title trim.
3.  **Start-of-Body Scrubbing**:
    - Iterates through the first few lines to remove bullet points (`*`) that look like navigation links (short lines with URLs).
4.  **Inline Sanitization**:
    - Removes "Audio generado..." block (case-insensitive).
    - Removes social share block ("enviar por email").
    - Flattens all markdown links `[Text](URL)` -> `Text`.
5.  **Footer Slice**:
    - Cuts at the earliest of known markers: "Ver enlaces de interés", "Comentarios -----------------", "Secciones Servicios".

## Verification Results
- **Sample Size**: 20 articles.
- **Outcome**:
    - Navigation menus completely removed.
    - Body text starts cleanly (often with the first real paragraph or bolded lead).
    - "Audio" noise stripped.
    - Footers cleanly removed.
    - Average reduction: ~60-75% (reflecting high noise levels in raw HTML).
