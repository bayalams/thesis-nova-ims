"""
10__embedder.py - Step 10: Document Embedder
=============================================

This script processes all our collected documents and creates embeddings.

WHAT IT DOES:
1. Loads all documents from data/articles/ and data/wiki/
2. Chunks long documents into smaller pieces
3. Creates embeddings using OpenAI API
4. Stores everything in ChromaDB (local vector database)

HOW TO RUN:
    # First, set your OpenAI API key
    export OPENAI_API_KEY="your_api_key_here"
    
    # Then run the embedder
    python 10__embedder.py

WHAT IS AN EMBEDDING?
    - An embedding is a list of numbers that represents the "meaning" of text
    - Similar texts have similar embeddings
    - We use embeddings to find documents related to a question

WHAT IS CHROMADB?
    - ChromaDB is a simple local vector database
    - It stores embeddings and lets us search for similar ones
    - No external server needed - everything is stored in a folder
"""

# =============================================================================
# IMPORTS
# =============================================================================

import json        # Built-in library to work with JSON data
import os          # Built-in library to work with files and folders
from datetime import datetime  # Built-in library to work with dates and times
from pathlib import Path       # Built-in library for file path handling

# External libraries (install with pip)
import chromadb                # Vector database (pip install chromadb)
from openai import AzureOpenAI

# =============================================================================
# CONFIGURATION
# =============================================================================

# Input directories (where our documents are)
NEWS_DIR = "data/articles"
WIKI_DIR = "data/wiki"

# Output directory for ChromaDB
CHROMA_DIR = "data/vectordb"

# Collection name in ChromaDB
COLLECTION_NAME = "tourism_knowledge"

# AzureOpenAI embedding model
EMBEDDING_MODEL = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

# Maximum chunk size (in characters)
# OpenAI recommends chunks of ~500-1000 tokens
# We use 2000 characters which is roughly 500 tokens
MAX_CHUNK_SIZE = 2000

# Overlap between chunks (to keep context)
CHUNK_OVERLAP = 200

# Maximum content length (in characters)
# Documents larger than this will be skipped (likely spam or scraping errors)
# 200,000 chars ≈ 50,000 tokens ≈ 100 chunks
MAX_CONTENT_LENGTH = 200000

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_openai_client():
    """
    Create an Azure OpenAI client.
    
    The credentials are read from environment variables.
    """
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    if not endpoint or not api_key:
        print("[ERROR] Azure OpenAI credentials not found!")
        print()
        print("Please set these environment variables:")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_API_KEY='your-api-key'")
        print()
        raise SystemExit(1)
    
    print("[INFO] Azure OpenAI credentials loaded")
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version
    )


def load_documents(source_filter=None):
    """
    Load all documents from our data directories.
    
    PARAMETERS:
    - source_filter: If provided, only load documents from this source
    
    RETURNS:
    - A list of dictionaries, each containing document data
    """
    documents = []
    
    # Load news articles
    if os.path.exists(NEWS_DIR):
        print(f"[INFO] Loading news articles from {NEWS_DIR}...")
        news_files = list(Path(NEWS_DIR).glob("*.json"))
        
        for filepath in news_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                
                # Filter by source if requested
                doc_source = doc.get("source")
                if source_filter and doc_source != source_filter:
                    continue
                
                # Extract the content we need
                # ONLY use cleaned text from 03__cleaner.py - no fallback to raw
                content = doc.get("text", "")
                
                if content and len(content) > 100:
                    documents.append({
                        "id": doc.get("id"),
                        "type": "news",
                        "source": doc.get("source"),
                        "title": doc.get("metadata", {}).get("title", ""),
                        "url": doc.get("link"),
                        "content": content,
                    })
            except Exception as e:
                print(f"[WARNING] Failed to load {filepath}: {e}")
        
        print(f"[INFO]   Loaded {len([d for d in documents if d['type'] == 'news'])} news articles")
    
    # Load Wikipedia articles
    if os.path.exists(WIKI_DIR):
        print(f"[INFO] Loading Wikipedia articles from {WIKI_DIR}...")
        wiki_files = list(Path(WIKI_DIR).glob("*.json"))
        
        for filepath in wiki_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                
                content = doc.get("content", "")
                
                if content and len(content) > 100:
                    documents.append({
                        "id": doc.get("id"),
                        "type": "wiki",
                        "source": "wikipedia",
                        "title": doc.get("title", ""),
                        "url": doc.get("url"),
                        "content": content,
                    })
            except Exception as e:
                print(f"[WARNING] Failed to load {filepath}: {e}")
        
        print(f"[INFO]   Loaded {len([d for d in documents if d['type'] == 'wiki'])} Wikipedia articles")
    
    print(f"[INFO] Total documents loaded: {len(documents)}")
    return documents


def chunk_text(text, chunk_size, overlap):
    """
    Split text into smaller chunks with overlap.
    
    WHY CHUNK?
    - LLMs have limited context windows
    - Smaller chunks = more precise retrieval
    - Overlap = keeps context between chunks
    
    PARAMETERS:
    - text: The text to split
    - chunk_size: Maximum size of each chunk
    - overlap: Number of characters to overlap
    
    RETURNS:
    - A list of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        # Get the chunk
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)
        
        # Move to next chunk (with overlap)
        start = end - overlap
    
    return chunks


def create_embedding(client, text):
    """
    Create an embedding for a piece of text using OpenAI API.
    
    PARAMETERS:
    - client: OpenAI client
    - text: The text to embed
    
    RETURNS:
    - A list of numbers (the embedding vector)
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    
    return response.data[0].embedding


def setup_chromadb(reset=False, source_filter=None):
    """
    Set up ChromaDB and create/get our collection.
    
    PARAMETERS:
    - reset: If True, delete the entire collection and start fresh.
    - source_filter: If provided (and not reset), delete only chunks from this source.
    
    RETURNS:
    - The ChromaDB collection
    """
    print(f"[INFO] Setting up ChromaDB in {CHROMA_DIR}...")
    
    # Create the ChromaDB client (persistent storage)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    if reset:
        # Delete existing collection if it exists (fresh start)
        try:
            client.delete_collection(name=COLLECTION_NAME)
            print("[INFO]   Deleted existing collection (RESET)")
        except:
            pass
        
        # Create new collection
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Portuguese Tourism Knowledge Base"}
        )
        print(f"[INFO]   Created NEW collection: {COLLECTION_NAME}")
    else:
        # Get or Create
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Portuguese Tourism Knowledge Base"}
        )
        print(f"[INFO]   Loaded existing collection: {COLLECTION_NAME}")
        
        if source_filter:
            # Delete existing chunks for this source so we can re-embed them
            try:
                print(f"[INFO]   Deleting existing chunks for source: {source_filter}")
                collection.delete(where={"source": source_filter})
                print(f"[INFO]   Deleted chunks for {source_filter}")
            except Exception as e:
                print(f"[WARNING] Failed to delete chunks for {source_filter}: {e}")
        
    return collection


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """
    Main function that runs the embedder.
    """
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Embed documents into ChromaDB")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset the database (delete everything) before starting"
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Only process articles from this source (e.g. SKIFT). Will delete and re-embed them."
    )
    parser.add_argument(
        "--no-chunk",
        action="store_true",
        help="Embed full articles without chunking (each article = 1 embedding)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("DOCUMENT EMBEDDER - Starting")
    print("=" * 60)
    print()
    
    # Step 1: Set up OpenAI client
    client = get_openai_client()
    print()
    
    
    # Step 2: Load all documents
    documents = load_documents(source_filter=args.source)
    print()
    
    if len(documents) == 0:
        print("[ERROR] No documents found! Run the data collection scripts first.")
        return
    
    # Step 3: Set up ChromaDB
    collection = setup_chromadb(reset=args.reset, source_filter=args.source)
    print()
    
    # Step 4: Process each document
    print("[INFO] Processing documents...")
    print()
    
    # Get existing documents to skip duplicates
    existing_ids = set()
    if not args.reset:
        try:
            # We fetch all IDs currently in the collection
            # "ids" is lightweight compared to "documents" or "embeddings"
            result = collection.get(include=[])
            existing_ids = set(result["ids"])
            print(f"[INFO] Found {len(existing_ids)} existing chunks in database")
        except Exception as e:
            print(f"[WARNING] Could not fetch existing IDs: {e}")
    
    total_chunks = 0
    skipped_docs = 0
    
    for i, doc in enumerate(documents, start=1):
        # Check if document is already processed
        # We check if the first chunk ID exists (doc_id + "_chunk_0")
        # This assumes if chunk 0 exists, the whole doc exists
        test_chunk_id = f"{doc['id']}_chunk_0"
        
        if test_chunk_id in existing_ids:
             print(f"[{i}/{len(documents)}] [SKIP] Already indexed: {doc['title'][:40]}...")
             skipped_docs += 1
             continue

        print(f"[{i}/{len(documents)}] Processing: {doc['title'][:50]}...")
        
        # Skip very large documents (likely spam or scraping errors)
        content_length = len(doc["content"])
        if content_length > MAX_CONTENT_LENGTH:
            print(f"[SKIP]   Document too large ({content_length:,} chars > {MAX_CONTENT_LENGTH:,} max)")
            print()
            continue
        
        # Chunk the document (or use full article if --no-chunk)
        if args.no_chunk:
            chunks = [doc["content"]]  # Full article as single chunk
            print(f"[INFO]   Using full article (no chunking)")
        else:
            chunks = chunk_text(doc["content"], MAX_CHUNK_SIZE, CHUNK_OVERLAP)
            print(f"[INFO]   Split into {len(chunks)} chunks")
        
        # Process each chunk
        for j, chunk in enumerate(chunks):
            # Create unique ID for this chunk
            chunk_id = f"{doc['id']}_chunk_{j}"
            
            # Create embedding
            embedding = create_embedding(client, chunk)
            
            # Store in ChromaDB
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{
                    "doc_id": doc["id"],
                    "type": doc["type"],
                    "source": doc["source"],
                    "title": doc["title"],
                    "url": doc["url"] or "",
                    "chunk_index": j,
                    "total_chunks": len(chunks),
                }]
            )
        
        total_chunks += len(chunks)
        print(f"[INFO]   Added to database")
        print()
    
    # Step 5: Print summary
    print("-" * 60)
    print()
    print("=" * 60)
    print("DOCUMENT EMBEDDER - Finished")
    print("=" * 60)
    print()
    print(f"Documents processed: {len(documents)}")
    print(f"  - Newly embedded: {len(documents) - skipped_docs}")
    print(f"  - Skipped (already exists): {skipped_docs}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Database location: {CHROMA_DIR}")
    print()


# =============================================================================
# RUN THE SCRIPT
# =============================================================================

if __name__ == "__main__":
    main()
