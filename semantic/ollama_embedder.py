#!/usr/bin/env python3
"""
Ollama Embedder - Simple wrapper for Ollama embeddings

Uses the Ollama API to generate text embeddings.
"""

import os
import requests
from pathlib import Path

# Configuration
OLLAMA_API_URL = os.environ.get(
    "OLLAMA_API_URL", "http://localhost:11434/api/embeddings"
)
DEFAULT_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
DEFAULT_EMBEDDING_DIM = 768  # nomic-embed-text default


def ollama_available():
    """Check if Ollama is running and available."""
    try:
        resp = requests.get(
            os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/tags"),
            timeout=2,
        )
        return resp.status_code == 200
    except:
        return False


def generate_embedding(text: str, model: str = None) -> list:
    """Generate embedding for text using Ollama."""
    model = model or DEFAULT_MODEL

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": model,
                "prompt": text[:10000],  # Limit text length
            },
            timeout=60,
        )

        if response.status_code != 200:
            return None

        data = response.json()
        return data.get("embedding")

    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None


# For backward compatibility
class OllamaEmbedder:
    """Simple Ollama embedder class."""

    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL
        self.api_url = OLLAMA_API_URL

    def embed(self, text: str) -> list:
        """Generate embedding for text."""
        return generate_embedding(text, self.model)

    def __call__(self, text: str) -> list:
        """Generate embedding for text."""
        return self.embed(text)
