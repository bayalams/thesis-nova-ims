import re
from datetime import datetime
from email.utils import parsedate_to_datetime

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
            
        raw_date = str(raw_date).strip()
        
        # Try various formats
        fmts = [
            None, # RFC 2822 (parsedate_to_datetime)
            "iso", # ISO
            "%d %b %Y, %H:%M", # TPN format: 15 Jan 2026, 13:59
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y, %H:%M",
            "%a, %d %b %Y %H:%M:%S %z", # Spiegel format: Sat, 29 Nov 2025 ...
        ]
        
        for fmt in fmts:
            try:
                if fmt is None:
                    dt = parsedate_to_datetime(raw_date)
                elif fmt == "iso":
                    dt = datetime.fromisoformat(raw_date)
                else:
                    dt = datetime.strptime(raw_date, fmt)
                
                return dt.strftime("%Y-%m-%d")
            except Exception:
                continue
    
    # Try just the first 10 chars if it looks like YYYY-MM-DD
    for raw_date in candidates:
        if raw_date and len(str(raw_date)) >= 10:
             try:
                 s = str(raw_date)[:10]
                 datetime.strptime(s, "%Y-%m-%d")
                 return s
             except:
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
    Only trims if title appears early in the text (first 2000 chars) to avoid
    matching titles in recommended articles sections at the bottom.
    """
    if not title:
        return text
    
    # 1. Clean Title for matching
    clean_title = re.sub(r'<!\[CDATA\[|\]\]>', '', title).strip()
    
    if len(clean_title) < 10:
        return text

    # 2. Find in text
    idx = text.lower().find(clean_title.lower())
    
    # 3. Only trim if title appears in first 2000 chars (actual header region)
    # This prevents matching titles in "recommended articles" sections at the bottom
    if idx != -1 and idx < 2000:
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
