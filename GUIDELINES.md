# Development Guidelines

This project is designed to be **beginner-friendly** for someone with a "CS50's Introduction to Programming with Python" level of understanding.

## Code Style Rules

### Keep It Simple
- **No object-oriented programming** - Use simple functions, no classes
- **No threading/concurrency** - Sequential processing only
- **No complex Python patterns** - Avoid decorators, generators, context managers where not essential
- **No pandas** - Use built-in `json` and `csv` modules

### Verbose Logging
- **Every step must print what it's doing** - Use `print()` statements liberally
- **Explain what's happening** - "[INFO] Parsing feed: PUBLICO" not just running silently
- **Show progress** - "[1/10] Processing..." so user knows what's happening

### Heavy Comments
- **Comment every function** - Explain what it does, parameters, return values
- **Comment each step** - "Step 1: Load the feeds", "Step 2: Parse each entry"
- **Explain WHY** - Not just what the code does, but why we're doing it

### File Naming
- **Numbered prefixes** - `00__`, `01__`, `02__` to show pipeline order
- **Descriptive names** - `01__indexer.py` not `idx.py`

### Error Handling
- **Basic try/except only** - Print error and continue, don't crash
- **No complex retry logic** - Simple is better

## Example Code Style

```python
def fetch_article(url):
    """
    Fetch an article from a URL.
    
    PARAMETERS:
    - url: The article URL to fetch
    
    RETURNS:
    - The article content as a string, or None if failed
    """
    print(f"[INFO] Fetching: {url}")
    
    try:
        # Step 1: Make the request
        response = requests.get(url)
        
        # Step 2: Check if successful
        if response.ok:
            print(f"[INFO] Success! Got {len(response.text)} characters")
            return response.text
        else:
            print(f"[WARNING] Failed with status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None
```

## What to Avoid

❌ Don't use:
- Classes (unless absolutely necessary)
- Decorators
- List comprehensions (except simple ones)
- Lambda functions
- `*args` / `**kwargs`
- Threading or async/await
- Complex imports from other modules

✅ Do use:
- Simple functions
- for loops
- if/else statements
- print() for logging
- try/except for error handling
- Built-in libraries (json, os, hashlib, etc.)
