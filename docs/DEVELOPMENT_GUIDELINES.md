# ELF Development Guidelines

## Architecture Principles

### 1. Async/Await Pattern (MANDATORY)

**All newly developed components MUST use async/await pattern.**

**Rationale:**
- Non-blocking I/O is essential for system stability
- Prevents resource exhaustion under load
- Enables concurrent processing
- Required for SSE connections, database operations, and API calls

**Correct Pattern:**

```python
import asyncio
import aiohttp
from contextlib import asynccontextmanager

# Database operations (async)
async def store_heuristic_async(domain: str, rule: str, confidence: float):
    """Store heuristic asynchronously."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO heuristics (domain, rule, confidence) VALUES (?, ?, ?)",
            (domain, rule, confidence)
        )
        await conn.commit()

# API calls (async)
async def call_semantic_search_async(query: str):
    """Call semantic search API asynchronously."""
    timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            "http://localhost:5001/search",
            json={"query": query}
        ) as response:
            return await response.json()

# SSE connections (async)
async def consume_sse_stream():
    """Consume SSE stream asynchronously."""
    timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get("http://localhost:4096/event") as response:
            async for line in response.content:
                if line:
                    yield line.decode()

# File operations (async)
async def write_log_async(message: str):
    """Write log asynchronously."""
    async with aiofiles.open(LOG_FILE, mode='a') as f:
        await f.write(f"{message}\n")

# Main async function
async def main():
    """Main event loop."""
    tasks = [
        consume_sse_stream(),
        process_events()
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
```

**Incorrect Patterns (NOT ALLOWED in new code):**

```python
# ❌ Blocking database calls
def store_heuristic(domain: str, rule: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO heuristics ...")  # BLOCKS EVENT LOOP
    conn.close()

# ❌ Blocking API calls
def call_semantic_search(query: str):
    response = requests.get(url, timeout=5)  # BLOCKS EVENT LOOP
    return response.json()

# ❌ Blocking file operations
def write_log(message: str):
    with open(LOG_FILE, 'a') as f:
        f.write(message)  # BLOCKS EVENT LOOP
```

### 2. Timeout Guidelines (MANDATORY)

**All async operations MUST use relaxed timeout settings.**

#### Timeout Ranges

| Operation Type | Minimum | Recommended | Maximum |
|----------------|---------|-------------|---------|
| SSE connections | 300s (5 min) | 600s (10 min) | 600s |
| Database operations | 20s | 30-60s | 120s |
| API calls | 20s | 60-120s | 300s |
| File I/O | 15s | 20-30s | 60s |
| Semantic search | 30s | 60s | 120s |
| Ollama embeddings | 60s | 120s | 300s |

#### Timeout Examples

```python
import aiohttp

# ✅ Good - relaxed timeout for SSE
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=300)
) as session:
    async with session.get(sse_url) as response:
        # Process SSE stream
        pass

# ✅ Good - medium timeout for API calls
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=60)
) as session:
    result = await call_api_async(session)

# ✅ Good - long timeout for long-running operations
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=600)
) as session:
    long_result = await long_operation_async(session)

# ❌ Bad - aggressive timeout (causes failures)
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=5)
) as session:
    # This will timeout frequently on any slow operation
    result = await call_api_async(session)
```

### 3. Error Handling

**All async operations MUST have proper error handling.**

```python
async def safe_async_operation():
    """Safe async operation with error handling."""
    try:
        result = await risky_operation()
        return result
    except asyncio.TimeoutError:
        logger.error("Operation timed out - consider increasing timeout")
        raise
    except aiohttp.ClientError as e:
        logger.error(f"API client error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### 4. Connection Management

**Use connection pooling for repeated operations.**

```python
# ✅ Good - connection pooling
class SemanticSearchClient:
    """Semantic search client with connection pooling."""
    def __init__(self):
        self._session = None

    async def __aenter__(self):
        """Create session with connection pooling."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            connector=aiohttp.TCPConnector(
                limit=100,  # Max 100 concurrent connections
                limit_per_host=30,  # Max 30 connections per host
                ttl_dns_cache=300,  # Cache DNS for 5 minutes
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session."""
        await self._session.close()

    async def search(self, query: str):
        """Perform search."""
        async with self._session.post("/search", json={"query": query}) as response:
            return await response.json()

# Usage
async with SemanticSearchClient() as client:
    results = await client.search("my query")
```

### 5. Resource Cleanup

**Always clean up resources with async context managers.**

```python
# ✅ Good - proper cleanup
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()
# Session automatically closed

# ✅ Good - database cleanup
async with aiosqlite.connect(DB_PATH) as conn:
    await conn.execute("INSERT INTO ...")
    await conn.commit()
# Connection automatically closed

# ❌ Bad - resource leak
async def bad_resource_usage():
    session = aiohttp.ClientSession()  # Never closed
    response = await session.get(url)
    data = await response.json()
    # Session NOT closed - resource leak
```

---

## Component-Specific Guidelines

### EventBridge

- **SSE timeout:** 5-10 minutes minimum
- **Event processing:** Non-blocking
- **Hook execution:** Async with reasonable timeout (30-60s)

```python
# EventBridge configuration
SSE_TIMEOUT = 600  # 10 minutes
HOOK_TIMEOUT = 60   # 1 minute

async def process_event_async(event):
    """Process event asynchronously."""
    try:
        # Execute hooks with timeout
        await asyncio.wait_for(
            execute_hooks_async(event),
            timeout=HOOK_TIMEOUT
        )
    except asyncio.TimeoutError:
        logger.warning(f"Hook execution timed out for event: {event}")
```

### Semantic Search Daemon

- **API timeout:** 60 seconds minimum
- **Database timeout:** 30 seconds
- **Ollama timeout:** 2 minutes

```python
# Semantic daemon configuration
SEMANTIC_API_TIMEOUT = 60
DATABASE_TIMEOUT = 30
OLLAMA_TIMEOUT = 120

async def generate_embedding_async(text: str):
    """Generate embedding with relaxed timeout."""
    timeout = aiohttp.ClientTimeout(
        total=OLLAMA_TIMEOUT,
        connect=10,
        sock_read=60
    )
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(OLLAMA_API, json={"prompt": text}) as response:
            return await response.json()
```

### Learning Processor

- **Database operations:** Async (aiosqlite)
- **Semantic search:** Async with 60s timeout
- **Pattern matching:** Non-blocking

```python
# Learning processor configuration
DB_TIMEOUT = 30
SEMANTIC_SEARCH_TIMEOUT = 60

async def record_learning_async(learning: dict):
    """Record learning asynchronously."""
    async with aiosqlite.connect(DB_PATH, timeout=DB_TIMEOUT) as conn:
        await conn.execute(
            "INSERT INTO learnings (domain, rule, confidence) VALUES (?, ?, ?)",
            (learning['domain'], learning['rule'], learning['confidence'])
        )
        await conn.commit()
```

---

## Testing Guidelines

### Async Test Patterns

```python
import pytest
import aiohttp

@pytest.mark.asyncio
async def test_semantic_search():
    """Test semantic search asynchronously."""
    async with aiohttp.ClientSession() as session:
        response = await session.post(
            "http://localhost:5001/search",
            json={"query": "test"}
        )
        assert response.status == 200
        results = await response.json()
        assert "results" in results

@pytest.mark.asyncio
async def test_timeout_handling():
    """Test that timeout is handled gracefully."""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            slow_operation(),
            timeout=1.0  # Short timeout
        )
```

### Mock Async Operations

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    """Test with async mock."""
    mock_api_call = AsyncMock(return_value={"status": "ok"})

    result = await mock_api_call("test")
    assert result == {"status": "ok"}
    mock_api_call.assert_called_once_with("test")
```

---

## Performance Guidelines

### Connection Pooling

- Reuse connections when possible
- Set sensible connection limits
- Use DNS caching

```python
connector = aiohttp.TCPConnector(
    limit=100,          # Total connections
    limit_per_host=30,  # Connections per host
    ttl_dns_cache=300,  # DNS cache TTL
    keepalive_timeout=30,
)
```

### Concurrent Processing

- Use `asyncio.gather()` for independent operations
- Use `asyncio.Semaphore` for rate limiting
- Avoid blocking the event loop

```python
# Process multiple items concurrently
async def process_items_concurrently(items):
    """Process items concurrently."""
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
    tasks = [
        process_item_with_limit(item, semaphore)
        for item in items
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

async def process_item_with_limit(item, semaphore):
    """Process single item with semaphore limit."""
    async with semaphore:
        return await process_item(item)
```

---

## Checklist

Before committing new code:

- [ ] All I/O operations are async/await
- [ ] Timeouts are >= 20 seconds minimum
- [ ] Long operations have appropriate timeouts (up to 10 minutes)
- [ ] Resources are cleaned up properly (context managers)
- [ ] Error handling covers all async-specific exceptions
- [ ] Connection pooling is used where applicable
- [ ] Tests use `@pytest.mark.asyncio` decorator
- [ ] No blocking operations in async functions

---

**Last Updated:** 2026-02-11
**Version:** 1.0
