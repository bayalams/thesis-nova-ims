"""
03__cleaner.py - Step 3: Article Cleaner
=========================================

This script processes the raw scraped articles from Step 2 and applies specific cleaning rules.

WHAT IT DOES:
1. Reads JSON files from data/articles/
2. Extracts the raw HTML/Markdown content
3. Applies source-specific cleaners (from cleaners/)
4. Updates the JSON file with a "text" field containing the clean content
5. Keeps the original raw content for debugging/re-cleaning

HOW TO RUN:
    # Clean all articles
    python 03__cleaner.py

    # Clean specific source
    python 03__cleaner.py --source PUBLICO

    # Force re-clean all articles (overwrite existing "text" field)
    python 03__cleaner.py --force
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add current directory to path so we can import 'cleaners'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from cleaners import clean_and_enrich_text
except ImportError:
    print("[ERROR] Could not import 'cleaners' package. Make sure you are running from the project root.")
    sys.exit(1)

# Configuration
INPUT_DIR = "data/articles"

def process_article(filepath, force=False):
    """
    Load, clean, and save a single article.
    Returns: (status, source, title)
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check if already cleaned
        if not force and "text" in data and data["text"]:
            return "SKIPPED", data.get("source", "UNKNOWN"), filepath
            
        # Extract raw content
        # Scraper v2 saves 'scrapingbee' object with 'content'
        # Archive files use 'scrapingbee.body' instead
        if "scrapingbee" in data and "content" in data["scrapingbee"]:
            raw_text = data["scrapingbee"]["content"]
        elif "scrapingbee" in data and "body" in data["scrapingbee"]:
            raw_text = data["scrapingbee"]["body"]
        elif "content" in data: # Fallback for older format if exists
            raw_text = data["content"]
        else:
            print(f"[WARNING] No content found in {filepath}")
            return "ERROR", "UNKNOWN", filepath

        # Apply Cleaning
        metadata = data.get("metadata", {})
        # Ensure metadata has tags and source if missing (backfill)
        if "tags" not in metadata: metadata["tags"] = []
        # Add scraped_at to metadata for cleaners that need it (e.g., Skift)
        if "scraped_at" in data:
            metadata["scraped_at"] = data["scraped_at"]
        
        cleaned_text = clean_and_enrich_text(raw_text, metadata)
        
        # Check for empty result (filtered)
        if not cleaned_text.strip():
            # semantic decision: keep the file but text is empty?
            # Or mark as invalid?
            data["is_valid_article"] = False
            data["text"] = "" 
            # We save it anyway so we know we processed it
            status = "FILTERED"
        else:
            data["is_valid_article"] = True
            data["text"] = cleaned_text
            status = "CLEANED"
            
        # Save back to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return status, data.get("source", "UNKNOWN"), filepath

    except Exception as e:
        print(f"[ERROR] Failed to process {filepath}: {e}")
        return "ERROR", "UNKNOWN", filepath

def main():
    parser = argparse.ArgumentParser(description="Clean raw articles")
    parser.add_argument("--source", help="Limit to specific source (e.g., PUBLICO)")
    parser.add_argument("--force", action="store_true", help="Re-clean even if 'text' exists")
    args = parser.parse_args()
    
    print("="*60)
    print("ARTICLE CLEANER - Starting")
    print("="*60)
    
    # Find all JSON files
    all_files = list(Path(INPUT_DIR).glob("*.json"))
    
    if not all_files:
        print("[ERROR] No articles found in data/articles/")
        return

    # Filter by source if requested
    # We have to peek at the file or assume filename doesn't have source.
    # Actually, we can't easily filter by source without opening the file, 
    # unless we iterate all and check.
    
    files_to_process = all_files
    print(f"[INFO] Found {len(files_to_process)} files total.")
    
    # Processing
    stats = {"CLEANED": 0, "SKIPPED": 0, "FILTERED": 0, "ERROR": 0}
    
    # We'll need to read files to check source if filtering
    # Multi-threaded for speed (IO bound-ish, but json parsing is CPU)
    
    print(f"[INFO] Processing with 10 threads...")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_article, f, args.force): f for f in files_to_process}
        
        for i, future in enumerate(as_completed(futures), 1):
            f = futures[future]
            status, source, path = future.result()
            
            # Source filtering check (post-processing check effectively)
            if args.source and args.source.upper() not in source.upper():
                continue
                
            stats[status] += 1
            if status == "CLEANED":
                print(f"[{i}/{len(files_to_process)}] [CLEANED] {source}: {path.name}")
            elif status == "FILTERED":
                print(f"[{i}/{len(files_to_process)}] [FILTERED] {source}: {path.name} (Empty content)")
            elif status == "ERROR":
                print(f"[{i}/{len(files_to_process)}] [ERROR] {path.name}")
            
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Cleaned:  {stats['CLEANED']}")
    print(f"Filtered: {stats['FILTERED']} (Empty/Invalid)")
    print(f"Skipped:  {stats['SKIPPED']} (Already done)")
    print(f"Errors:   {stats['ERROR']}")

if __name__ == "__main__":
    main()
