"""
eTurboNews Cleaner
==================

Cleans articles from ETURBONEWS source.
These articles have author bios, promotional blocks, and footer widgets.
"""

import re


def clean_eturbonews(text, meta):
    """
    Cleaner for ETURBONEWS articles.
    """
    if not text:
        return ""
    
    # 0. Pre-processing: Remove known garbage lines
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        sline = line.strip()
        if not sline:
            filtered_lines.append(line)
            continue
        
        # Skip author byline
        if sline.startswith("Written by ["):
            continue
            
        # Skip separator lines
        if re.match(r'^-{3,}$', sline):
            continue
            
        # Skip promotional CTAs
        if "Register here and now" in sline:
            continue
        if "Still need tickets for" in sline:
            continue
        if "Click here" in sline and ("news to share" in sline or "tickets" in sline.lower()):
            continue
            
        filtered_lines.append(line)
    
    text = '\n'.join(filtered_lines)
    
    # 1. Footer Cleaning - cut at footer sections
    footer_markers = [
        "\n### You may also like",
        "\n### About the author",
        "\n### Leave a Comment",
        "\n#### Podcast",
        "\n#### Share",
        "\n#### Join us!",
        "\n#### Amazing Travel Awards",
        "\n#### Featured Posts",
        "\nCopy link",
        "\nFind any service",
        "\nOn March 2, 2026, the **World Tourism Network**",  # Promotional block
    ]
    
    first_idx = len(text)
    for marker in footer_markers:
        idx = text.find(marker)
        if idx != -1 and idx < first_idx:
            first_idx = idx
    
    text = text[:first_idx]
    
    # 2. Post-processing cleanup
    
    # Remove markdown images ![...](...) 
    text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)
    
    # Flatten links: [Text](URL) -> Text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove "Destinations International Home" standalone lines
    text = re.sub(r'^Destinations International Home$', '', text, flags=re.MULTILINE)
    
    # Remove quoted related article links like "> [Article Title](url)"
    text = re.sub(r'^\s*>\s*\[.*?\]\(.*?\)\s*$', '', text, flags=re.MULTILINE)
    
    # Remove title suffix noise like "1 Travel & Tourism News..."
    text = re.sub(r'\d+\s*Travel & Tourism News[^"]*"\)', '', text)
    
    # Clean up multiple blank lines
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()
