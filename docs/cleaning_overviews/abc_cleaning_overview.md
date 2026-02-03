# ABC_ESPANA Cleaning Overview

This document details the specific cleaning logic applied to `ABC_ESPANA` articles to prepare them for the RAG pipeline. The verification reports confirm that these steps produce high-quality, distraction-free text.

## 1. Metadata Enrichment
Before cleaning the body text, we ensure critical metadata is captured.

### Tags Extraction
*   **Strategy**: We attempt to find tags in the following order:
    1.  `metadata['tags']` (often empty for ABC).
    2.  `metadata['keywords']` or `metadata['sections']`.
    3.  **Fallback (Text Extraction)**: Scans the article footer *before* trimming for the **"Temas:"** or **"Más temas:"** section. It extracts the refined tag list (ignoring noise) and injects it into the `TAGS:` header.

### Date Handling
*   **Strategy**: Dates are parsed from metadata (`published`, `updated`, or `Date` header) and standardized to `YYYY-MM-DD`.
*   **Body Cleanup**: All date lines (e.g., `22/12/2025` or `Actualizado a las...`) are **removed** from the body text to prevent redundancy.

## 2. Structural Cleaning

### Header Trimming
*   **Title Search**: Locates the article title in the raw text and removes all navigational content (menu bars, breadcrumbs) appearing *before* it.
*   **Repeated Title**: If the title is repeated immediately at the start of the body text (common in this source), the duplicate is removed.

### Footer Trimming
The article is truncated immediately upon encountering any of the following footer triggers.
*   **Constraint**: Triggers must appear at the **start of a line** (`^\s*`) to avoid false positives (e.g., matching "Vocento" inside a URL string).

**Triggers:**
*   `Reportar un error`
*   `Últimas Noticias`
*   `Copyright © DIARIO ABC`
*   `Vocento`
*   `Temas:` / `Más temas:`
*   `Artículo solo para suscriptores`
*   `Límite de sesiones alcanzadas` (and variations like `#### Límite...`)

## 3. Inline Noise Removal

### Image & Visual Artifacts
*   **Markdown Images**: All `![Alt Text](URL)` patterns are completely stripped.
*   **Residual Artifacts**: Specific cleanup for broken image text anomalies ending in `@diario_abc.jpg)`.
*   **Separators**: Visual separator lines (`=====`, `-----`, `_____`) are removed.

### Link Handling
*   **Goal**: Distraction-free reading flow.
*   **Inline Links**: Flattened to plain text.
    *   *Before*: `found in the [city of Madrid](url)...`
    *   *After*: `found in the city of Madrid...`
*   **Standalone Links**: Lines consisting *only* of a link (e.g., "Related: [Article](...)") are deleted.
*   **Widget Headers**: Markdown headers containing links (e.g., `### [Read Also](...)`) are deleted.

### Specific Junk Patterns
Regex filters are used to remove specific recurring noise:
*   Subscription prompts ("Esta funcionalidad es sólo para suscriptores")
*   Login buttons ("Iniciar sesión", "Si ya estás suscrito...")
*   Social Media shares ("* Facebook", "* X", "* Whatsapp", "* Copiar enlace")
*   Lottery Widgets ("Comprobar Lotería", "Número", "Importe")

## 4. Final Output Format
The resulting text block is formatted as:
```text
DATE: YYYY-MM-DD
TAGS: Tag1, Tag2, Tag3
TITLE: Article Title

[Cleaned Body Text...]
```
