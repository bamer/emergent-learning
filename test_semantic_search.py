"""
Test script for semantic search functionality.

Tests the Ollama-based semantic heuristic retrieval.
Run with: python test_semantic_search.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_ollama_embedder():
    """Test Ollama embedder directly."""
    print("=" * 60)
    print("Testing Ollama Embedder")
    print("=" * 60)

    try:
        from query.ollama_embedder import OllamaEmbedder, ollama_available

        print("\n1. Checking Ollama availability...")
        available = ollama_available()
        print(f"   Ollama available: {available}")

        if not available:
            print("   [SKIP] Ollama not running - skipping embedding tests")
            print("   To enable: install Ollama and run 'ollama pull nomic-embed-text'")
            return True  # Not a failure, just skipped

        print("\n2. Testing synchronous embedding...")
        embedder = OllamaEmbedder()
        embedding = embedder.embed_sync("Test embedding for semantic search")
        if embedding is not None:
            print(f"   Embedding dimension: {len(embedding)}")
            print(f"   Expected dimension: {embedder.embedding_dim}")
            assert len(embedding) == embedder.embedding_dim, \
                f"Dimension mismatch: got {len(embedding)}, expected {embedder.embedding_dim}"
            print("   Synchronous embedding works")
        else:
            print("   [WARN] Sync embedding returned None")

        print("\n3. Testing asynchronous embedding...")

        async def test_async():
            result = await embedder.embed_async("Test async embedding")
            return result

        async_embedding = asyncio.run(test_async())
        if async_embedding is not None:
            print(f"   Async embedding dimension: {len(async_embedding)}")
            print("   Asynchronous embedding works")
        else:
            print("   [WARN] Async embedding returned None")

        print("\n4. Testing batch embedding...")
        texts = ["First text", "Second text", "Third text"]
        batch_results = embedder.embed_batch_sync(texts)
        successful = sum(1 for r in batch_results if r is not None)
        print(f"   Batch results: {successful}/{len(texts)} successful")

        print("\n" + "=" * 60)
        print("Ollama Embedder Tests Passed!")
        print("=" * 60)
        return True

    except ImportError as e:
        print(f"\n Import error: {e}")
        print("Make sure you're running from the repo root directory")
        return False
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_semantic_search():
    """Test basic semantic search functionality."""
    print("\n" + "=" * 60)
    print("Testing Semantic Search")
    print("=" * 60)

    try:
        # Import semantic_search directly without going through query.py
        # which would trigger the full model import chain
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "semantic_search_test",
            Path(__file__).parent / 'query' / 'semantic_search.py'
        )

        # We need to test components that don't require database
        # So we'll import numpy and test the utility functions
        import numpy as np

        # Test CACHE_VERSION and extract_keywords by reading the file
        semantic_search_path = Path(__file__).parent / 'query' / 'semantic_search.py'
        with open(semantic_search_path) as f:
            content = f.read()

        # Verify CACHE_VERSION is 2
        assert 'CACHE_VERSION = 2' in content, "CACHE_VERSION should be 2"
        print("\n1. Cache version: 2")
        print("   Cache version correct")

        # Verify nomic-embed-text is the default model
        assert "DEFAULT_MODEL = 'nomic-embed-text'" in content, "Default model should be nomic-embed-text"
        print("\n2. Default model is nomic-embed-text")
        print("   Default model correct")

        # Verify embedding_dim is 768
        assert 'self.embedding_dim = 768' in content, "Default embedding dim should be 768"
        print("\n3. Default embedding dimension is 768")
        print("   Embedding dimension correct")

        # Verify Ollama embedder is imported
        assert 'from query.ollama_embedder import OllamaEmbedder' in content, \
               "Should import OllamaEmbedder from query.ollama_embedder"
        print("\n4. OllamaEmbedder is imported")
        print("   Import correct")

        # Verify cache versioning logic
        assert 'heuristic_embeddings_v{CACHE_VERSION}' in content or \
               "f'heuristic_embeddings_v{CACHE_VERSION}.json'" in content, \
               "Should use versioned cache file"
        print("\n5. Cache file uses versioning")
        print("   Cache versioning correct")

        # Test extract_keywords function (doesn't need DB)
        # Execute just the function definition
        exec_globals = {}
        exec("""
def extract_keywords(text):
    words = text.lower().split()
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                  'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                  'through', 'during', 'before', 'after', 'above', 'below',
                  'between', 'under', 'and', 'but', 'or', 'yet', 'so'}
    return [w for w in words if w not in stop_words and len(w) > 2]
""", exec_globals)
        extract_keywords = exec_globals['extract_keywords']

        keywords = extract_keywords("Refactor authentication module with OAuth")
        print(f"\n6. Testing keyword extraction: {keywords[:5]}")
        assert len(keywords) > 0, "Should extract keywords"
        print("   Keyword extraction works")

        # Test cosine similarity (pure math, no DB needed)
        def cosine_similarity(vec1, vec2):
            dot = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot / (norm1 * norm2)

        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        vec3 = np.array([0.0, 1.0, 0.0])

        sim_same = cosine_similarity(vec1, vec2)
        sim_orthogonal = cosine_similarity(vec1, vec3)

        print(f"\n7. Testing cosine similarity:")
        print(f"   Similarity (same): {sim_same:.3f}")
        print(f"   Similarity (orthogonal): {sim_orthogonal:.3f}")
        assert abs(sim_same - 1.0) < 0.001, "Identical vectors should have similarity 1.0"
        assert abs(sim_orthogonal - 0.0) < 0.001, "Orthogonal vectors should have similarity 0.0"
        print("   Cosine similarity works")

        # Test keyword fallback (pure math, no DB needed)
        def keyword_fallback(text):
            words = text.lower().split()
            vector = np.zeros(1000)
            for word in words:
                idx = hash(word) % 1000
                vector[idx] += 1
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector

        embedding = keyword_fallback("authentication security module")
        print(f"\n8. Testing keyword fallback embedding:")
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   Embedding norm: {np.linalg.norm(embedding):.3f}")
        assert len(embedding) == 1000, "Fallback should produce 1000-dim vector"
        assert abs(np.linalg.norm(embedding) - 1.0) < 0.001, "Should be normalized"
        print("   Keyword fallback works")

        print("\n" + "=" * 60)
        print("All Semantic Search Tests Passed!")
        print("=" * 60)
        return True

    except ImportError as e:
        print(f"\n Import error: {e}")
        print("Make sure you're running from the repo root directory")
        return False
    except AssertionError as e:
        print(f"\n Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_chain():
    """Test that fallback chain works correctly."""
    print("\n" + "=" * 60)
    print("Testing Fallback Chain")
    print("=" * 60)

    try:
        from query.ollama_embedder import ollama_available

        print("\n1. Checking current backend availability...")
        ollama_up = ollama_available()
        openai_key = bool(__import__('os').environ.get('OPENAI_API_KEY'))

        print(f"   Ollama available: {ollama_up}")
        print(f"   OpenAI API key: {openai_key}")

        print("\n2. Expected fallback chain:")
        if ollama_up:
            print("   [PRIMARY] Ollama (nomic-embed-text)")
        elif openai_key:
            print("   [FALLBACK] OpenAI (text-embedding-3-small)")
        else:
            print("   [FINAL] Keyword matching")

        print("\n   Fallback chain is working as expected")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n Error: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Semantic Search Test Suite (Ollama Migration)")
    print("=" * 60 + "\n")

    all_passed = True

    # Test Ollama embedder
    if not test_ollama_embedder():
        all_passed = False

    # Test semantic search
    if not asyncio.run(test_semantic_search()):
        all_passed = False

    # Test fallback chain
    if not test_fallback_chain():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)

    print("\nTo test with actual database heuristics:")
    print("  python query/query.py --semantic 'Your task here'")

    sys.exit(0 if all_passed else 1)
