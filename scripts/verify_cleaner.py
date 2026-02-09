#!/usr/bin/env python3
"""
Cleaner Verification Script
============================
Generates a markdown report showing before/after cleaning for a specific source.
Includes full metadata: date, title, source, tags.
"""

import json
import re
import sys
from pathlib import Path

# Add src to path for imports
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from cleaners.dispatcher import clean_and_enrich_text

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "articles"


def extract_tags_from_text(text):
    """Try to extract tags from article text if none exist."""
    tags = []
    
    # Noise phrases to skip
    noise_phrases = ['for this article', 'page not found', 'the content you requested']
    
    # Pattern 1: Markdown bullet list of tags like "* [Tag](/tag/...)"
    tag_links = re.findall(r'\*\s*\[([^\]]+)\]\(/(?:tag|etiqueta|topic|en/tag)/[^\)]+\)', text)
    for t in tag_links:
        t = t.strip()
        if t and t not in tags and len(t) < 50:
            if not any(noise in t.lower() for noise in noise_phrases):
                tags.append(t)
    
    # Pattern 2: "Tags: tag1, tag2" but NOT "Keywords for this article"
    tag_match = re.search(r'(?:Tags|Related topics)[:\s]+([^\n]+)', text, re.IGNORECASE)
    if tag_match and not tags:  # Only use if we didn't find link-based tags
        raw_tags = tag_match.group(1)
        # Split by comma or |
        for t in re.split(r'[,|]', raw_tags):
            t = t.strip()
            # Remove markdown link syntax
            t = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', t)
            # Skip noise and short/long strings
            if t and 3 < len(t) < 50 and not t.startswith('http'):
                if not any(noise in t.lower() for noise in noise_phrases):
                    tags.append(t)
    
    return tags[:10]  # Limit to 10 tags


def find_articles_by_source(source_name, limit=5):
    """Find articles by source name, skipping failed scrapes."""
    articles = []
    for filepath in DATA_DIR.glob("*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('source', '').upper() == source_name.upper():
                text = data.get('text', '')
                # Skip failed scrapes (API limit, short text, etc)
                if len(text) < 500:
                    continue
                if 'API calls limit reached' in text:
                    continue
                if 'enable JavaScript' in text and len(text) < 200:
                    continue
                articles.append((filepath, data))
                if len(articles) >= limit:
                    break
        except Exception as e:
            continue
    return articles


def get_metadata(data, raw_text):
    """Extract metadata from article data, with fallback extraction from text."""
    metadata = data.get('metadata', {})
    
    # Title
    title = data.get('title') or metadata.get('title') or ''
    
    # Source
    source = data.get('source') or metadata.get('source') or ''
    
    # Date - try multiple fields
    date = metadata.get('date') or metadata.get('published') or metadata.get('updated') or ''
    if not date:
        date = data.get('scraped_at', '')[:10] if data.get('scraped_at') else ''
    
    # Tags - try multiple fields
    tags = data.get('tags') or metadata.get('tags') or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    
    # If no tags, try to extract from text
    if not tags:
        tags = extract_tags_from_text(raw_text)
    
    # Final noise filter - remove any bad tags that slipped through
    noise = ['for this article', 'page not found', 'the content you requested', 
             'keywords for this article', 'related topics']
    tags = [t for t in tags if t.lower() not in noise and len(t) > 2]
    
    # URL
    url = data.get('link') or metadata.get('link') or ''
    
    return {
        'title': title,
        'source': source,
        'date': date,
        'tags': tags,
        'url': url,
        'link': url,
    }


def generate_verification_report(source_name, limit=5):
    """Generate a markdown verification report for a source."""
    articles = find_articles_by_source(source_name, limit)
    
    if not articles:
        return f"# {source_name} Verification\n\nNo articles found for source: {source_name}"
    
    report_lines = [
        f"# {source_name} Cleaner Verification",
        f"",
        f"Found {len(articles)} articles for verification.",
        f"",
    ]
    
    for i, (filepath, data) in enumerate(articles, 1):
        raw_text = data.get('text', '')
        meta = get_metadata(data, raw_text)
        
        # Create a copy for the cleaner (it may modify meta)
        cleaner_meta = dict(meta)
        
        # Clean the text
        cleaned_text = clean_and_enrich_text(raw_text, cleaner_meta)
        
        # Get updated tags from cleaner if available
        final_tags = cleaner_meta.get('tags', meta['tags'])
        if isinstance(final_tags, list):
            tags_display = ', '.join(final_tags) if final_tags else '(none extracted)'
        else:
            tags_display = str(final_tags) if final_tags else '(none extracted)'
        
        # Reduction percentage
        if raw_text and cleaned_text:
            reduction = ((len(raw_text) - len(cleaned_text)) / len(raw_text)) * 100
            reduction_str = f" ({reduction:.1f}% reduction)"
        else:
            reduction_str = ""
        
        report_lines.extend([
            f"---",
            f"",
            f"## Article {i}: {meta['title'][:100]}",
            f"",
            f"### Metadata",
            f"",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **Source** | {meta['source']} |",
            f"| **Date** | {meta['date']} |",
            f"| **Title** | {meta['title'][:80]}{'...' if len(meta['title']) > 80 else ''} |",
            f"| **Tags** | {tags_display} |",
            f"| **URL** | {meta['url']} |",
            f"| **Raw Length** | {len(raw_text)} chars |",
            f"| **Cleaned Length** | {len(cleaned_text) if cleaned_text else 0} chars{reduction_str} |",
            f"",
            f"### Raw Text (BEFORE cleaning)",
            f"",
            f"```",
            raw_text,
            f"```",
            f"",
            f"### Cleaned Text (AFTER cleaning)",
            f"",
            f"```",
            cleaned_text if cleaned_text else "(EMPTY - article filtered out)",
            f"```",
            f"",
        ])
    
    return "\n".join(report_lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_cleaner.py SOURCE_NAME [limit]")
        print("Example: python verify_cleaner.py DW_NEWS 5")
        sys.exit(1)
    
    source = sys.argv[1].upper()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    report = generate_verification_report(source, limit)
    print(report)
