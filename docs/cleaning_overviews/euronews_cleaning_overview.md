# Euronews Cleaning Overview

## 1. Source Identification
- **Source ID**: `EURONEWS_NEWS`
- **Language**: Portuguese

## 2. Identified Noise Patterns
### Header
- **Massive Social Block**: A large block of text containing navigation links ("Ir para a navegação"), social media sharing buttons ("Flipboard", "Facebook", etc.), and author/date metadata.
- **Artifacts**: Markdown image links (`![twitter...`) and "Link copiado!" messages.
- **Separator**: Often a long separator line (`------`) or a lead summary separates the header from the body.

### Footer
- **Navigation/Related**: "Mais vistas", "Notícias relacionadas", "A nossa escolha".
- **Comentários**: "Comentários" section often marks the end of the body.
- **Legal/Accessibility**: "To use this website...", "Ir para os atalhos de acessibilidade".

### Inline
- **Ad/UI Noise**: "Publicidade", "Partilhar".
- **Orphaned Social Lines**: "Facebook", "Twitter", "Flipboard".

## 3. Cleaning Strategy (`clean_euronews.py`)
### Video Skip
- **Logic**: Articles are identified as video pages if the URL contains `/video/`.
- **Action**: These are skipped entirely (cleaner returns `None`) as they lack substantial textual content.

### Header Cleaning
- **Logic**: Aggressively searches for the *last* social media link pattern (e.g., `![twitter](...)`) or "Link copiado!" text in the first 5000 characters.
- **Action**: Cuts everything purely before this point to remove the massive navigation/social block, while preserving the lead paragraph if it appears after (or ensuring body content is safe).

### Footer Cleaning
- **Markers**: Slices text at the *first* occurrence of:
  - "Mais vistas"
  - "Notícias relacionadas"
  - "A nossa escolha"
  - "Comentários" (Strict check to avoid header links)
  - "Ir para os atalhos de acessibilidade"
  - "Copyright ©"

### Tag Extraction
- **Method**: Extracts tags from the footer area using the pattern `* [Tag Name](URL)`.
- **Policy**: Tags are extracted to metadata and NOT prepended to the body.

### Inline Cleaning
- **Filtering**: Removal of specific noise lines:
  - Social platform names (Facebook, Twitter, etc.)
  - Navigation links ("Ir para...")
  - **Metadata**: Removes "De [Author]" lines (handling non-breaking spaces `\xa0`) and timestamp lines (e.g., "05/01/2026 - ...").
  - **Artifacts**: Removes lines containing only link artifacts like `[Comentários](...)`.

### Post-Processing
- Removes trailing `[` artifacts.
- Removes residual markdown images.
- Removes broken link artifacts (lines starting with `](`, e.g., sharing links).
## 4. Verification Results
- **Header**: Successfully removed the large social/navigation block.
- **Body**: Clean text, retaining article structure.
- **Tags**: Extracted successfully.
- **Reduction**: Significant reduction (30-80%) due to the massive size of the original header noise.
