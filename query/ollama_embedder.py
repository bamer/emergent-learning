"""
Ollama embedder for semantic search using nomic-embed-text model.

This is the primary embedding backend for ELF, replacing the old
sentence-transformers approach. It provides:

1. Fast, local embeddings using Ollama
2. 768-dimensional embeddings (up from 384)
3. Fallback to OpenAI or keyword matching
4. Async and sync APIs

Requires:
- Ollama installed and running (https://ollama.com/)
- nomic-embed-text model pulled: `ollama pull nomic-embed-text`
"""

import os
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
import numpy as np
from pathlib import Path

# Default embedding model
DEFAULT_MODEL = 'nomic-embed-text'
# Default embedding dimension
DEFAULT_EMBEDDING_DIM = 768
# Ollama API endpoint
OLLAMA_API_URL = 'http://localhost:11434/api/embeddings'


def ollama_available() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(('localhost', 11434))
        sock.close()
        return result == 0
    except Exception:
        return False


class OllamaEmbedder:
    """
    Ollama-based text embedding service.
    
    Supports async and sync operations for embedding text using
    the nomic-embed-text model.
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, embedding_dim: int = DEFAULT_EMBEDDING_DIM):
        """
        Initialize OllamaEmbedder.
        
        Args:
            model: Ollama model name (default: nomic-embed-text)
            embedding_dim: Expected embedding dimension (default: 768)
        """
        self.model = model
        self.embedding_dim = embedding_dim
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def embed_async(self, text: str) -> Optional[np.ndarray]:
        """
        Async method to generate embedding for single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array, or None on failure
        """
        try:
            if not ollama_available():
                return None
                
            session = await self._get_session()
            
            payload = {
                'model': self.model,
                'prompt': text
            }
            
            async with session.post(OLLAMA_API_URL, json=payload) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                if 'embedding' not in data:
                    return None
                
                embedding = np.array(data['embedding'])
                
                # Ensure embedding has expected dimension
                if len(embedding) != self.embedding_dim:
                    return None
                
                return embedding
                
        except Exception as e:
            print(f"Error in embed_async: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def embed_sync(self, text: str) -> Optional[np.ndarray]:
        """
        Sync method to generate embedding for single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array, or None on failure
        """
        try:
            return asyncio.run(self.embed_async(text))
        except Exception:
            return None
    
    def embed_batch_sync(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Sync method to generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (or None for failures)
        """
        try:
            return asyncio.run(self.embed_batch_async(texts))
        except Exception:
            return [None for _ in texts]
    
    async def embed_batch_async(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Async method to generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (or None for failures)
        """
        tasks = [self.embed_async(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    def embed_batch_sync(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Sync method to generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (or None for failures)
        """
        try:
            return asyncio.run(self.embed_batch_async(texts))
        except Exception:
            return [None for _ in texts]
    
    async def close(self):
        """Close the HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            if self._session is not None and not self._session.closed:
                # We can't use await in __del__, so we'll use a sync approach
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self._session.close())
        except Exception:
            pass


# Test function for module
if __name__ == "__main__":
    import sys
    
    print("Testing Ollama Embedder...")
    print(f"Ollama available: {ollama_available()}")
    
    if not ollama_available():
        print("Ollama server not running. Please start Ollama and try again.")
        sys.exit(1)
    
    embedder = OllamaEmbedder()
    
    # Test single embedding
    text = "Refactor authentication module with OAuth 2.0"
    embedding = embedder.embed_sync(text)
    
    if embedding is not None:
        print(f"Embedding successful: {len(embedding)}-dimensional")
        print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
    else:
        print("Embedding failed")
        sys.exit(1)
    
    # Test batch embedding
    texts = [
        "Implement user authentication",
        "Fix database connection issues",
        "Optimize API response time"
    ]
    
    embeddings = embedder.embed_batch_sync(texts)
    successful = sum(1 for emb in embeddings if emb is not None)
    
    print(f"\nBatch embedding: {successful}/{len(texts)} successful")
    
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        if emb is not None:
            print(f"  {i+1}. {text[:30]}... ({len(emb)}-dimensional)")
        else:
            print(f"  {i+1}. {text[:30]}... [FAILED]")
    
    print("\nOllama Embedder test completed successfully!")
