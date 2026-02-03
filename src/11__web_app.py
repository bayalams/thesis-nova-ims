"""
11__web_app.py - Step 11: Web Interface for RAG
================================================

This script runs a simple web interface for asking questions.

WHAT IT DOES:
1. Shows a web page with a question input
2. When you ask a question, it:
   - Searches the vector database for relevant documents
   - Sends the documents + question to OpenAI
   - Shows the answer with citations

HOW TO RUN:
    # First, set your OpenAI API key
    export OPENAI_API_KEY="your_api_key_here"
    
    # Then run the web app (with Wikipedia articles - default)
    python 11__web_app.py
    
    # Or run WITHOUT Wikipedia articles (news only)
    python 11__web_app.py --no-wikipedia
    
    # Open in browser: http://localhost:9999

COMMAND LINE OPTIONS:
    --use-wikipedia   Include Wikipedia articles in search (default)
    --no-wikipedia    Exclude Wikipedia articles, only use news

REQUIREMENTS:
    - Run 10__embedder.py first to create the vector database
"""

# =============================================================================
# IMPORTS
# =============================================================================

import argparse    # Built-in library to parse command line arguments
import json        # Built-in library to work with JSON data
import os          # Built-in library to work with files and folders

# External libraries (install with pip)
import chromadb                    # Vector database
from flask import Flask, request, render_template_string  # Web framework
from openai import OpenAI          # OpenAI API

# =============================================================================
# GLOBAL FLAG FOR WIKIPEDIA ARTICLES
# =============================================================================
# This will be set by command line arguments
# True = include Wikipedia articles in search
# False = only use news articles (DEFAULT)
USE_WIKIPEDIA = False

# =============================================================================
# CONFIGURATION
# =============================================================================

# ChromaDB settings
CHROMA_DIR = "data/vectordb"
COLLECTION_NAME = "tourism_knowledge"

# OpenAI settings
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"

# How many documents to retrieve
TOP_K = 10

# =============================================================================
# HTML TEMPLATE
# =============================================================================
# We keep the HTML simple and inline for beginner-friendliness

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Portuguese Tourism Assistant</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #2c3e50;
        }
        .question-form {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
        }
        input[type="text"]:focus {
            border-color: #3498db;
            outline: none;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #2980b9;
        }
        .answer {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .answer h2 {
            color: #27ae60;
            margin-top: 0;
        }
        .answer-text {
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .sources {
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .sources h3 {
            margin-top: 0;
            color: #7f8c8d;
        }
        .source-item {
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #3498db;
        }
        .source-item a {
            color: #3498db;
            text-decoration: none;
        }
        .source-item a:hover {
            text-decoration: underline;
        }
        .source-type {
            font-size: 12px;
            color: #95a5a6;
            text-transform: uppercase;
        }
        .chunks {
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border-left: 3px solid #ffc107;
        }
        .chunks h3 {
            margin-top: 0;
            color: #856404;
        }
        .chunk-item {
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #ddd; /* Default grey for unused */
            transition: all 0.2s;
        }
        .chunk-item.used {
            border-left-color: #27ae60;
            background-color: #f0fff4;
            box-shadow: 0 2px 5px rgba(39, 174, 96, 0.1);
        }
        .chunk-header {
            font-weight: bold;
            color: #555;
            margin-bottom: 8px;
            display: flex;
            justify_content: space-between;
            align_items: center;
        }
        .badge {
            font-size: 10px;
            padding: 3px 6px;
            border-radius: 4px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .badge.used {
            background: #27ae60;
            color: white;
        }
        .badge.unused {
            background: #95a5a6;
            color: white;
        }
        .chunk-content {
            font-size: 14px;
            line-height: 1.5;
            color: #333;
            max-height: 300px; /* Taller */
            overflow-y: auto;
            white-space: pre-wrap;
            border-top: 1px solid #eee;
            margin-top: 8px;
            padding-top: 8px;
        }
        .chunk-meta {
            font-size: 12px;
            color: #6c757d;
            margin-top: 8px;
        }
    </style>
</head>
<body>
    <h1>🇵🇹 Portuguese Tourism Assistant</h1>
    <p>Ask me anything about travel, tourism, and culture in Portugal and Europe!</p>
    
    <div class="question-form">
        <form method="POST">
            <input type="text" name="question" placeholder="What are the best places to visit in Lisbon?" 
                   value="{{ question or '' }}" autofocus>
            <button type="submit">Ask Question</button>
        </form>
    </div>
    
    {% if answer %}
    <div class="answer">
        <h2>Answer</h2>
        <div class="answer-text">{{ answer }}</div>
        
        {% if chunks %}
        <div class="chunks">
            <h3>🔍 Retrieved Chunks (Evaluation)</h3>
            <p style="font-size: 14px; color: #856404; margin-bottom: 15px;">
                These are the {{ chunks|length }} chunks retrieved from the database. 
                <br>
                <strong>Precision:</strong> {{ chunks|selectattr('is_used')|list|length }} used / {{ chunks|length }} retrieved.
            </p>
            {% for chunk in chunks %}
            <div class="chunk-item {{ 'used' if chunk.is_used else 'unused' }}">
                <div class="chunk-header">
                    <span>
                        Chunk #{{ chunk.display_index }} - {{ chunk.title }}
                    </span>
                    {% if chunk.is_used %}
                        <span class="badge used">USED [Source {{ chunk.display_index }}]</span>
                    {% else %}
                        <span class="badge unused">UNUSED</span>
                    {% endif %}
                </div>
                
                <div class="chunk-content">{{ chunk.content }}</div>
                
                <div class="chunk-meta">
                    <strong>Source:</strong> {{ chunk.source }} | 
                    <strong>Type:</strong> {{ chunk.type }} | 
                    <strong>Chunk Part:</strong> {{ chunk.chunk_index + 1 }}/{{ chunk.total_chunks }}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if sources %}
        <div class="sources">
            <h3>📚 Sources Used</h3>
            {% for source in sources %}
            <div class="source-item">
                <span class="source-type">{{ source.type }}</span>
                <strong>{{ source.title }}</strong>
                {% if source.url %}
                <br><a href="{{ source.url }}" target="_blank">{{ source.url }}</a>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if reasoning %}
        <div class="sources" style="border-left: 3px solid #9b59b6; margin-top: 15px;">
            <h3>🧠 Reasoning</h3>
            <div style="line-height: 1.6; white-space: pre-wrap;">{{ reasoning }}</div>
        </div>
        {% endif %}
    </div>
    {% endif %}
</body>
</html>
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_openai_client():
    """
    Create an OpenAI client.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("[ERROR] OpenAI API key not found!")
        print()
        print("Please set the OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY='your_api_key_here'")
        print()
        raise SystemExit(1)
    
    return OpenAI(api_key=api_key)


def get_chromadb_collection():
    """
    Get the ChromaDB collection.
    """
    if not os.path.exists(CHROMA_DIR):
        print("[ERROR] Vector database not found!")
        print()
        print("Please run 10__embedder.py first to create the database.")
        print()
        raise SystemExit(1)
    
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)
    
    return collection


def search_documents(collection, client, question, top_k):
    """
    Search for documents relevant to the question.
    
    PARAMETERS:
    - collection: ChromaDB collection
    - client: OpenAI client
    - question: The user's question
    - top_k: Number of results to return
    
    RETURNS:
    - A list of relevant document chunks with metadata
    """
    print(f"[INFO] Searching for documents related to: {question[:50]}...")
    
    # Step 1: Check if we should include Wikipedia articles
    if USE_WIKIPEDIA:
        print("[INFO] Wikipedia articles: ENABLED")
    else:
        print("[INFO] Wikipedia articles: DISABLED (only using news)")
    
    # Step 2: Create embedding for the question
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=question
    )
    question_embedding = response.data[0].embedding
    
    # Step 3: Search ChromaDB
    # If USE_WIKIPEDIA is False, we filter to only 'news' type
    if USE_WIKIPEDIA:
        # Include all document types (news + wiki)
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=top_k
        )
    else:
        # Only include news articles (exclude wiki)
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=top_k,
            where={"type": "news"}
        )
    
    # Step 4: Format results
    documents = []
    for i in range(len(results["ids"][0])):
        documents.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
        })
    
    print(f"[INFO] Found {len(documents)} relevant chunks")
    return documents


def generate_answer(client, question, documents):
    """
    Generate an answer using OpenAI with the retrieved documents.
    
    PARAMETERS:
    - client: OpenAI client
    - question: The user's question
    - documents: List of relevant document chunks
    
    RETURNS:
    - The generated answer text
    """
    print("[INFO] Generating answer...")
    
    # Build the context from documents
    context_parts = []
    for i, doc in enumerate(documents, start=1):
        meta = doc["metadata"]
        context_parts.append(f"[Source {i}: {meta['title']}]\n{doc['content']}\n")
    
    context = "\n---\n".join(context_parts)
    
    # Build the prompt
    # The system prompt instructs the AI to cite sources for EVERY piece of information
    # This makes it easy for the user to verify facts against the original sources
    system_prompt = """You are a helpful assistant specializing in Portuguese and European tourism.

Answer the user's question based on the provided sources. Be informative and helpful.

IMPORTANT - CITATION RULES:
1. You MUST cite the source for EVERY piece of information you provide
2. Use inline citations in the format [Source N] after each fact or claim
3. Example: "Lisbon is the capital of Portugal [Source 1] and has a population of around 500,000 [Source 2]."
4. If multiple sources confirm the same fact, cite all of them: [Source 1, 3]
5. NEVER state a fact without a citation - this is critical for verification

If the sources don't contain enough information to fully answer the question, say so clearly and only provide information that IS supported by the sources.

FORMAT YOUR RESPONSE LIKE THIS:
[Your answer with citations here]

REASONING:
[Explain your reasoning process here - which sources you found most relevant, how you combined information, any gaps you noticed, and why you structured the answer the way you did]"""

    user_prompt = f"""Here are relevant sources from our knowledge base:

{context}

---

User Question: {question}

Please provide a helpful answer based on the sources above. Remember to cite [Source N] after EVERY piece of information. Then explain your reasoning after the REASONING: marker."""

    # Call OpenAI
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=1500  # Increased to allow room for reasoning
    )
    
    full_response = response.choices[0].message.content
    print("[INFO] Answer generated")
    
    # Split the response into answer and reasoning
    # Look for the REASONING: marker
    if "REASONING:" in full_response:
        parts = full_response.split("REASONING:", 1)
        answer = parts[0].strip()
        reasoning = parts[1].strip()
    else:
        answer = full_response
        reasoning = None
    
    return answer, reasoning


# =============================================================================
# FLASK APP
# =============================================================================

# Create Flask app
app = Flask(__name__)

# Initialize clients (done once at startup)
openai_client = None
chroma_collection = None


@app.route("/", methods=["GET", "POST"])
def home():
    """
    Main page handler.
    Shows the question form and handles submissions.
    """
    global openai_client, chroma_collection
    
    question = None
    answer = None
    sources = None
    reasoning = None
    
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        
        if question:
            print()
            print("=" * 60)
            print(f"[QUESTION] {question}")
            print("=" * 60)
            
            # Search for relevant documents
            documents = search_documents(
                chroma_collection, 
                openai_client, 
                question, 
                TOP_K
            )
            
            # Generate answer (now returns answer and reasoning)
            answer, reasoning = generate_answer(openai_client, question, documents)
            
            # Identify which chunks were actually used based on citations
            # We look for [Source 1], [Source 2], [Source 1, 3], etc.
            used_indices = set()
            if answer:
                import re
                # Find all [Source ...] patterns and extract all numbers within
                # This handles both [Source 1] and [Source 1, 3, 4]
                source_blocks = re.findall(r"\[Source[s]?\s*([^\]]+)\]", answer, re.IGNORECASE)
                for block in source_blocks:
                    # Extract all numbers from within the block
                    numbers = re.findall(r"(\d+)", block)
                    for num in numbers:
                        try:
                            idx = int(num) - 1
                            if 0 <= idx < len(documents):
                                used_indices.add(idx)
                        except:
                            pass
            
            # Prepare chunks for evaluation display
            chunks = []
            for i, doc in enumerate(documents):
                meta = doc["metadata"]
                is_used = i in used_indices
                
                chunks.append({
                    "content": doc["content"], # FULL CONTENT
                    "title": meta["title"],
                    "source": meta["source"],
                    "type": meta["type"],
                    "chunk_index": meta.get("chunk_index", 0),
                    "total_chunks": meta.get("total_chunks", 1),
                    "is_used": is_used,
                    "display_index": i + 1
                })
            
            # Extract unique sources for display
            seen_titles = set()
            sources = []
            for i, doc in enumerate(documents):
                meta = doc["metadata"]
                title = meta["title"]
                if title not in seen_titles:
                    seen_titles.add(title)
                    is_used = i in used_indices
                    sources.append({
                        "title": title,
                        "type": meta["type"],
                        "source": meta["source"],
                        "url": meta.get("url", ""),
                        "is_used": is_used
                    })
            
            print()
    
    return render_template_string(
        HTML_TEMPLATE,
        question=question,
        answer=answer,
        chunks=chunks if request.method == "POST" and question else None,
        sources=sources,
        reasoning=reasoning
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    """
    Main function that runs the web app.
    """
    global openai_client, chroma_collection, USE_WIKIPEDIA
    
    # Step 1: Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Portuguese Tourism Assistant - RAG Web App"
    )
    
    # Create mutually exclusive group for wikipedia flag
    # This means you can use --use-wikipedia OR --no-wikipedia, but not both
    wiki_group = parser.add_mutually_exclusive_group()
    wiki_group.add_argument(
        "--use-wikipedia",
        action="store_true",
        help="Include Wikipedia articles in search results"
    )
    wiki_group.add_argument(
        "--no-wikipedia",
        action="store_true",
        help="Exclude Wikipedia articles, only use news articles (default)"
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Set the global flag based on arguments
    # Default is False (no Wikipedia), unless --use-wikipedia is passed
    if args.use_wikipedia:
        USE_WIKIPEDIA = True
    else:
        USE_WIKIPEDIA = False
    
    print("=" * 60)
    print("PORTUGUESE TOURISM ASSISTANT - Starting")
    print("=" * 60)
    print()
    
    # Step 2: Show configuration
    if USE_WIKIPEDIA:
        print("[CONFIG] Wikipedia articles: ENABLED")
    else:
        print("[CONFIG] Wikipedia articles: DISABLED (news only)")
    print()
    
    # Step 3: Initialize OpenAI client
    print("[INFO] Initializing OpenAI client...")
    openai_client = get_openai_client()
    print()
    
    # Step 4: Initialize ChromaDB
    print("[INFO] Loading vector database...")
    chroma_collection = get_chromadb_collection()
    print(f"[INFO] Collection loaded: {COLLECTION_NAME}")
    print()
    
    # Step 5: Start the web server
    print("[INFO] Starting web server...")
    print()
    print("=" * 60)
    print("🌐 Open in your browser: http://localhost:9999")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    app.run(host="0.0.0.0", port=9999, debug=False)


if __name__ == "__main__":
    main()