"""
01__indexer.py - Step 1: RSS Feed Indexer
==========================================

This script reads RSS feeds and saves article links to JSONL files.

WHAT IT DOES:
1. Reads the list of RSS feeds from 00__rss_feeds.py
2. For each feed, downloads the RSS XML and parses it
3. Extracts: title, link, published date, summary
4. Creates a unique fingerprint (hash) for each article
5. Saves everything to a JSONL file (one JSON object per line)

HOW TO RUN:
    python 01__indexer.py

OUTPUT:
    data/links/20260101_150700_PUBLICO.jsonl
    data/links/20260101_150700_EXPRESSO.jsonl
    ... (one file per feed)
"""

# =============================================================================
# IMPORTS
# =============================================================================
# We import the libraries we need at the top of the file

import feedparser  # Library to parse RSS feeds (pip install feedparser)
import hashlib     # Built-in library to create unique fingerprints (hashes)
import json        # Built-in library to work with JSON data
import os          # Built-in library to work with files and folders
from datetime import datetime  # Built-in library to work with dates and times

import argparse    # Built-in library for command line arguments

# Import our feed configuration from Step 0
from importlib.machinery import SourceFileLoader

# =============================================================================
# CONFIGURATION
# =============================================================================

# Where to save the output files
OUTPUT_DIR = "data/links"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_feeds():
    """
    Load the RSS feeds from 00__rss_feeds.py
    
    We use SourceFileLoader because the file name starts with a number,
    which makes it tricky to import normally.
    """
    print("[INFO] Loading feed configuration from 00__rss_feeds.py...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    feeds_file = os.path.join(script_dir, "00__rss_feeds.py")
    
    # Load the module
    loader = SourceFileLoader("rss_feeds", feeds_file)
    feeds_module = loader.load_module()
    
    print(f"[INFO] Loaded {len(feeds_module.RSS_FEEDS)} feeds")
    return feeds_module.RSS_FEEDS


def create_fingerprint(title, link, published):
    """
    Create a unique fingerprint (hash) for an article.
    
    WHY WE DO THIS:
    - The same article might appear in multiple runs
    - The fingerprint helps us identify duplicates later
    - We use SHA-256 which creates a unique 64-character string
    
    PARAMETERS:
    - title: The article title
    - link: The article URL
    - published: The publication date
    
    RETURNS:
    - A 64-character hexadecimal string (the fingerprint)
    """
    # Combine the three values into one string
    data = f"{title}|{link}|{published}"
    
    # Create a SHA-256 hash of the combined string
    fingerprint = hashlib.sha256(data.encode("utf-8")).hexdigest()
    
    return fingerprint


def is_article_fresh(published_parsed, max_age_days=90):
    """
    Check if an article is fresh enough to be indexed.
    
    PARAMETERS:
    - published_parsed: time.struct_time object from feedparser
    - max_age_days: Maximum age in days (default: 90)
    
    RETURNS:
    - True if fresh (or no date), False if too old
    """
    if not published_parsed:
        return True # Keep if no date allowed (or assume fresh)
        
    # Convert struct_time to datetime
    try:
        dt_pub = datetime(*published_parsed[:6])
        dt_now = datetime.now()
        delta = dt_now - dt_pub
        
        if delta.days > max_age_days:
            return False
            
        return True
    except Exception as e:
        print(f"[WARNING] Date parsing error: {e}. Defaulting to 'fresh'.")
        return True # Fallback: keep on error


def parse_feed(feed_name, feed_url, max_age_days=90):
    """
    Download and parse an RSS feed.
    
    PARAMETERS:
    - feed_name: The name of the feed (e.g., "PUBLICO")
    - feed_url: The URL of the RSS feed
    - max_age_days: Skip articles older than this (default: 90)
    
    RETURNS:
    - A list of dictionaries, each containing article data
    """
    print(f"[INFO] Parsing feed: {feed_name}")
    print(f"[INFO]   URL: {feed_url}")
    
    # Step 1: Download and parse the RSS feed
    # feedparser does all the hard work for us!
    feed = feedparser.parse(feed_url)
    
    # Step 2: Check if the feed has any entries
    if not feed.entries:
        print(f"[WARNING] No entries found in feed: {feed_name}")
        return []
    
    print(f"[INFO]   Found {len(feed.entries)} entries")
    
    # Step 3: Extract ALL available data from each entry
    # Different feeds have different fields, so we capture everything!
    articles = []
    skipped_count = 0
    
    for entry in feed.entries:
        # Check freshness first
        if not is_article_fresh(entry.get("published_parsed"), max_age_days):
            skipped_count += 1
            continue

        # Basic fields (always try to get these)
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = entry.get("published", None)
        summary = entry.get("summary", None)
        
        # Author information
        # Some feeds use "author", others use "authors" (list)
        author = entry.get("author", None)
        authors = entry.get("authors", None)
        
        # Tags/Categories
        # This is usually a list of dictionaries with "term" field
        tags_raw = entry.get("tags", [])
        tags = []
        if tags_raw:
            for tag in tags_raw:
                if isinstance(tag, dict):
                    tags.append(tag.get("term", str(tag)))
                else:
                    tags.append(str(tag))
        
        # Media content (images, videos)
        # Common in news feeds for article thumbnails
        media_content = entry.get("media_content", None)
        media_thumbnail = entry.get("media_thumbnail", None)
        
        # Additional common fields
        content = entry.get("content", None)  # Full content if available
        updated = entry.get("updated", None)  # Last update time
        id_field = entry.get("id", None)      # Unique ID from feed
        
        # Create a fingerprint for this article
        fingerprint = create_fingerprint(title, link, published)
        
        # Build the article dictionary with ALL available metadata
        article = {
            "source": feed_name,
            "title": title,
            "link": link,
            "published": published,
            "summary": summary,
            "author": author,
            "authors": authors,
            "tags": tags if tags else None,
            "media_content": media_content,
            "media_thumbnail": media_thumbnail,
            "content": content,
            "updated": updated,
            "feed_id": id_field,
            "fingerprint": fingerprint,
            "indexed_at": datetime.now().isoformat()
        }
        
        articles.append(article)
    
    if skipped_count > 0:
        print(f"[INFO]   Skipped {skipped_count} stale articles (> {max_age_days} days old)")
        
    return articles


def save_to_jsonl(articles, feed_name, output_dir):
    """
    Save articles to a JSONL file.
    
    WHAT IS JSONL?
    - JSONL = JSON Lines
    - Each line in the file is a separate JSON object
    - Easy to read line by line (good for large files)
    
    FILES ARE ORGANIZED BY SOURCE:
    - data/links/PUBLICO/20260101_152601.jsonl
    - data/links/EXPRESSO/20260101_152602.jsonl
    
    PARAMETERS:
    - articles: List of article dictionaries
    - feed_name: Name of the feed (used for subfolder)
    - output_dir: Base directory to save files
    
    RETURNS:
    - The path to the saved file
    """
    # Step 1: Create the source-specific subdirectory
    # Example: data/links/PUBLICO/
    source_dir = os.path.join(output_dir, feed_name)
    os.makedirs(source_dir, exist_ok=True)
    
    # Step 2: Create the filename with timestamp (no source name needed in filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jsonl"
    filepath = os.path.join(source_dir, filename)
    
    # Step 3: Write each article as a JSON line
    print(f"[INFO]   Saving to: {filepath}")
    
    with open(filepath, "w", encoding="utf-8") as f:
        for article in articles:
            # Convert the dictionary to a JSON string
            json_line = json.dumps(article, ensure_ascii=False)
            # Write the line followed by a newline character
            f.write(json_line + "\n")
    
    print(f"[INFO]   Saved {len(articles)} articles")
    
    return filepath


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """
    Main function that runs the indexer.
    
    This function:
    1. Loads the feed configuration
    2. Parses each feed
    3. Saves the results to JSONL files
    """
    parser = argparse.ArgumentParser(description="RSS Feed Indexer")
    parser.add_argument("--max-age-days", type=int, default=90, help="Skip articles older than X days (default: 90)")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"RSS FEED INDEXER - Starting (Max Age: {args.max_age_days} days)")
    print("=" * 60)
    print()
    
    # Step 1: Load the feeds
    feeds = load_feeds()
    
    print()
    print("-" * 60)
    print()
    
    # Step 2: Process each feed
    total_articles = 0
    saved_files = []
    
    for feed in feeds:
        feed_name = feed["name"]
        feed_url = feed["url"]
        
        try:
            # Parse the feed with max_age filtering
            articles = parse_feed(feed_name, feed_url, max_age_days=args.max_age_days)
            
            # Save to JSONL file (only if we have articles)
            if articles:
                filepath = save_to_jsonl(articles, feed_name, OUTPUT_DIR)
                saved_files.append(filepath)
                total_articles += len(articles)
            
            print()
            
        except Exception as e:
            # If something goes wrong, print the error and continue
            print(f"[ERROR] Failed to process {feed_name}: {e}")
            print()
    
    # Step 3: Print summary
    print("-" * 60)
    print()
    print("=" * 60)
    print("RSS FEED INDEXER - Finished")
    print("=" * 60)
    print()
    print(f"Total feeds processed: {len(feeds)}")
    print(f"Total files saved: {len(saved_files)}")
    print(f"Total articles indexed: {total_articles}")
    print()
    print("Output directory:", OUTPUT_DIR)
    print()


# =============================================================================
# RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    main()
