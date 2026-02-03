import re
import json
from datetime import datetime
from email.utils import parsedate_to_datetime

# ==============================================================================
#           STANDALONE ABC_ESPANA CLEANING SCRIPT
# ==============================================================================

def get_best_date(doc_json):
    """
    Tries to extract a best-guess publication date from various metadata fields.
    Returns YYYY-MM-DD string or 'Unknown Date'.
    """
    meta = doc_json.get("metadata", {}) or {}
    headers = meta.get("headers", {}) or {}

    candidates = [
        meta.get("published"),
        meta.get("updated"),
        headers.get("Date")
    ]

    for raw_date in candidates:
        if not raw_date:
            continue
        try:
            # ROI: RFC 2822 (e.g., "Tue, 23 Dec 2025 22:45:27 +0100")
            dt = parsedate_to_datetime(raw_date)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
        
        try:
            # ISO Format (e.g., "2025-12-23T22:45:27")
            dt = datetime.fromisoformat(raw_date)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    return "Unknown Date"

def get_tags(doc_json):
    """
    Extracts tags as a comma-separated string.
    """
    meta = doc_json.get("metadata", {}) or {}
    tags = meta.get("tags")

    # Fallback to 'keywords' or 'sections' or 'section'
    if not tags:
        tags = meta.get("keywords")
    if not tags:
        tags = meta.get("sections")
    if not tags:
        # Sometimes 'section' is a single string or dict
        sec = meta.get("section")
        if sec:
            tags = [sec] if isinstance(sec, str) else []

    if not tags:
        return ""

    if isinstance(tags, list):
        # Filter out dicts if any, keep strings
        valid_tags = [t for t in tags if isinstance(t, str)]
        return ", ".join(valid_tags)
    
    return str(tags)

def trim_header_by_title(text, title):
    """
    Locates the title in the text and removes everything before it.
    Input title is cleaned of CDATA noise inside this function for matching.
    """
    if not title:
        return text
    
    # 1. Clean Title for matching
    clean_title = re.sub(r'<!\[CDATA\[|\]\]>', '', title).strip()
    
    if len(clean_title) < 10:
        return text

    # 2. Find in text
    idx = text.lower().find(clean_title.lower())
    if idx != -1:
        # print(f"[DEBUG] Found title at {idx}")
        return text[idx:]
    
    return text

def remove_inline_noise(text):
    """
    Removes common inline noise like ads, navigation links, breadcrumbs.
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    # Common triggers
    noise_keywords = [
        "read comments", "share on", "whatsapp", "facebook", "twitter",
        "subscribe", "iniciar sesión", "log in", "sign up", 
        "reportar un error", "publicidad", "advertisement", "sponsor",
        "all rights reserved", "copyright", 
        "privacidade", "consentimento", "cookies", "aceitar", "concordo",
        "partilhar", "copiar link", "subscrever", "já é subscritor"
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # A. Remove Markdown Images: ![...](...)
        if stripped.startswith("![") and "](" in stripped:
            continue
            
        # B. Remove "Functional" Link Lists e.g. "* [Home](...)"
        if re.match(r'^[\*\-\+]? ?\[.*?\]\(.*?\)\s*$', stripped):
            continue

        # C. Remove Breadcrumbs e.g. "Home > News > Portugal"
        if " > " in stripped and len(stripped) < 100:
            if "Home" in stripped or "News" in stripped or "Economia" in stripped:
                continue

        # D. Keyword Filtering
        lower_line = stripped.lower()
        if any(keyword in lower_line for keyword in noise_keywords):
            continue
            
        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines)

def extract_abc_tags(text):
    """
    Attempts to extract tags from the 'Más temas:' or 'Temas:' section 
    often found in the footer of ABC articles before it gets cut.
    """
    tags = []
    # Locate the start of the themes block
    # We look for "Temas:" or "Más temas:" at start of line, optionally with a bullet
    match = re.search(r'^\s*[\*\-]?\s*(?:Más\s+)?Temas:\s*$', text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return []
    
    # Start scanning lines after the match
    start_pos = match.end()
    rest = text[start_pos:]
    
    for line in rest.split('\n'):
        if not line.strip():
            continue
        
        # ABC tags usually appear as bulleted links: "* [TagName](URL)"
        # Regex to capture the text inside the square brackets
        # matches: * [TagName](...) or - [TagName](...)
        link_match = re.match(r'^\s*[\*\-]\s*\[([^\]]+)\]', line)
        if link_match:
            tags.append(link_match.group(1).strip())
        elif line.strip().startswith('*') or line.strip().startswith('-'):
            # Maybe just text? "* TagName"
            clean_line = line.strip().lstrip('*-').strip()
            if clean_line and "reportar un error" not in clean_line.lower():
                 tags.append(clean_line)
        else:
            # If we hit a line that doesn't look like a list item, stop.
            # (Unless it's immediately after triggers? usually they are list items)
            # Check if it's another footer trigger
            if "Reportar un error" in line or "Vocento" in line:
                break
                
    return tags

def clean_abc_espana(text, meta):
    # 1. Header Trim (Title)
    title = meta.get('title', '').strip()
    text = trim_header_by_title(text, title)

    # 1.1 Remove Repeated Title in Body (if it exists at the start)
    # Often scrapingbee output keeps the H1. If we have it in metadata, we strip it from body to avoid duplication.
    # We normalized title for matching in trim_header, now let's perform a removal.
    clean_title = re.sub(r'<!\[CDATA\[|\]\]>', '', title).strip()
    if clean_title:
        # Check if text starts with title (ignoring case/whitespace)
        if text.lstrip().lower().startswith(clean_title.lower()):
            # Find the end of the title in the text
            # We use find because we know it starts with it (ignoring case), but we want the exact length to cut
            # Actually, simpler: just regex replace the start if it matches.
            # But let's stick to simple slicing if we find the index.
            idx = text.lower().find(clean_title.lower())
            if idx != -1:
                # Remove title and any immediate following newlines/separators
                text = text[idx+len(clean_title):]

    # 2. Specific Footer Trimming
    # ABC ends with "Reportar un error", "Últimas Noticias", or specific subscription blocks.
    # We use regex to be robust against Markdown formatting (e.g. #### Límite...)
    # IMPORTANT: Anchor to start of line (^\s*) to avoid matching URLs (e.g. .../vocento.abc/...) or body text.
    footer_triggers_regex = [
        r'^\s*Reportar un error',
        r'^\s*Últimas Noticias',
        r'^\s*Copyright\s*©\s*DIARIO\s*ABC',
        r'^\s*Vocento',
        r'^\s*Temas:', 
        r'^\s*Más temas:',
        r'^\s*Artículo solo para suscriptores', 
        r'^\s*(#+\s*)?Límite de sesiones alcanzadas', # Matches "Límite..." or "#### Límite..."
        r'^\s*(#+\s*)?Has superado el límite de sesiones'
    ]
    
    # We join them into one big regex for "find first occurrence of any"
    # We look for the pattern, and cut from the start of the match.
    # We use (?:...) for non-capturing groups around patterns.
    combined_footer_pat = "|".join(f"(?:{p})" for p in footer_triggers_regex)
    
    match = re.search(combined_footer_pat, text, flags=re.IGNORECASE | re.MULTILINE)
    if match:
        # Debug: print(f"Cutting at {match.group()} index {match.start()}")
        text = text[:match.start()]

    # 3. ABC Specific Inline Noise Removal
    
    # Remove Markdown Images COMPLETELY before link flattening
    # Pattern: ![Alt](Url "Title") OR ![Alt](Url)
    # We allow newlines in the [...] part using (?s) or just regular . if valid. 
    # But usually the issue is multiline. Let's stick to inline first.
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # Specific cleanup for residual ABC image anomalies (e.g. "-U...-758x470@diario_abc.jpg)")
    # This matches lines that look like broken image file paths ending in )
    text = re.sub(r'.*@diario_abc\.jpg\)\s*$', '', text, flags=re.MULTILINE)

    # Remove DATES from body (User Request: "date should only be in metadata")
    # Formats: "01/01/2026", "01/01/2026 a las 02:01h.", "Actualizado a las..."
    date_patterns = [
        r'^\s*\d{1,2}/\d{1,2}/\d{4}\s*$', # Simple Date
        r'^\s*\d{1,2}/\d{1,2}/\d{4}\s+a\s+las\s+\d{1,2}:\d{2}h\.?\s*$', # Date + Time
        r'^\s*Actualizado\s+.*$' # Update lines
    ]
    for dp in date_patterns:
        text = re.sub(dp, '', text, flags=re.IGNORECASE | re.MULTILINE)
    # Remove long separator lines (dashes OR equals OR underscores)
    # User Request: "separation markers like ====="
    text = re.sub(r'^\s*[-=_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove "Read Also" / "Related" blocks that appear as Markdown headers with links or list items
    # Example: ### [Title](Link) or ### [Title](Link "Tooltip")
    # We must be aggressive here. If a line is a header and contains a link, it's likely a widget in this context.
    text = re.sub(r'^#+\s*\[.*?\]\(.*?\)\s*$', '', text, flags=re.MULTILINE)

    # Remove simple link lines often found in related news lists: "* [Title](Link)"
    text = re.sub(r'^\s*[\*\-]\s*\[.*?\]\(.*?\)\s*$', '', text, flags=re.MULTILINE)
    
    # User Request: "links in the body of the text"
    # Option A: Flatten them ([text](url) -> text) - Good for reading flow
    # Option B: Remove lines that are JUST links
    
    # 1. Remove lines that are ONLY a link (with optional whitespace or bullet)
    # This catches "Related: [Title](Url)" if it sits on its own line
    text = re.sub(r'^\s*>?\s*\[.*?\]\(.*?\)\s*$', '', text, flags=re.MULTILINE)
    
    # 2. Flatten remaining inline links in the body to just their text
    # Pattern: [Anchor Text](URL "Optional Title") -> Anchor Text
    # We use a non-greedy match for the square brackets and parentheses
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove subscription/login prompts and social junk
    abc_junk_patterns = [
        r'Esta funcionalidad es sólo para registrados',
        r'Esta funcionalidad es sólo para suscriptores',
        r'Si ya estás suscrito, inicia sesión',
        r'Suscribete',
        r'Iniciar sesión',
        r'\* Copiar enlace',
        r'\* Facebook',
        r'\* X',
        r'\* Whatsapp',
        r'\* Email',
        r'Comprobar Lotería Navidad.*',
        r'^Número\s*$', # Lottery widget header
        r'^Importe\s*$', # Lottery widget header
        r'^Comprobar\s*$', # Lottery widget button text
        r'Almería\s*This functionality.*', # Stray location tags if any
    ]
    
    for pattern in abc_junk_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

    # 4. Universal Inline
    text = remove_inline_noise(text)
    
    return text

def clean_and_enrich_abc(text, meta):
    """
    Main entry point for ABC cleaning.
    """
    if not text:
        return ""
    
    # 0. SKIP VIDEOS
    link = meta.get('link', '')
    if '/video/' in link or 'www.nytimes.com/video' in link:
        return ""

    # Source check (Redundant if using this script specifically, but good for safety)
    source = meta.get('source', '').upper()
    if 'ABC_ESPANA' not in source:
         # Fallback or warning? For now just proceed as if it is ABC or return generic
         pass

    cleaned_body = clean_abc_espana(text, meta)

    # Context Injection
    title = meta.get('title', '').strip()
    title = re.sub(r'<!\[CDATA\[|\]\]>', '', title).strip()

    date_str = get_best_date({'metadata': meta})
    
    # TAGS: Try metadata first, then fallback to text extraction
    tags_str = get_tags({'metadata': meta})
    if not tags_str:
        extracted = extract_abc_tags(text) # Use original text before cleaning
        if extracted:
            tags_str = ", ".join(extracted)

    header = f"DATE: {date_str}\n"
    if tags_str:
        header += f"TAGS: {tags_str}\n"
    header += f"TITLE: {title}\n"
    header += "\n"

    return header + cleaned_body
