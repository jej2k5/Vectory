"""Embedding providers for generating vector representations of text."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from app.config import settings
from app.utils.logger import logger


class EmbeddingProvider:
    """Multi-provider embedding generation."""

    @staticmethod
    def get_embedding(text: str, model: str | None = None, dimension: int = 1536) -> list[float]:
        """Generate an embedding for a single text."""
        model = model or settings.DEFAULT_EMBEDDING_MODEL

        if settings.OPENAI_API_KEY and model.startswith("text-embedding"):
            return EmbeddingProvider._openai_embedding(text, model)

        # Fallback to deterministic mock embeddings
        return EmbeddingProvider._mock_embedding(text, dimension)

    @staticmethod
    def get_batch_embeddings(
        texts: list[str], model: str | None = None, dimension: int = 1536
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        model = model or settings.DEFAULT_EMBEDDING_MODEL

        if settings.OPENAI_API_KEY and model.startswith("text-embedding"):
            return EmbeddingProvider._openai_batch_embeddings(texts, model)

        return [EmbeddingProvider._mock_embedding(t, dimension) for t in texts]

    @staticmethod
    def _openai_embedding(text: str, model: str) -> list[float]:
        """Generate embedding using OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            logger.error("OpenAI embedding failed: {}", e)
            raise

    @staticmethod
    def _openai_batch_embeddings(texts: list[str], model: str) -> list[list[float]]:
        """Generate batch embeddings using OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(input=texts, model=model)
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error("OpenAI batch embedding failed: {}", e)
            raise

    @staticmethod
    def _mock_embedding(text: str, dimension: int = 1536) -> list[float]:
        """Generate a deterministic mock embedding from text."""
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        vector = rng.randn(dimension).astype(float)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    @staticmethod
    def get_available_models() -> list[dict[str, Any]]:
        """Return list of available embedding models."""
        models = []
        if settings.OPENAI_API_KEY:
            models.extend([
                {"name": "text-embedding-3-small", "provider": "openai", "dimensions": 1536},
                {"name": "text-embedding-3-large", "provider": "openai", "dimensions": 3072},
                {"name": "text-embedding-ada-002", "provider": "openai", "dimensions": 1536},
            ])
        if settings.COHERE_API_KEY:
            models.extend([
                {"name": "embed-english-v3.0", "provider": "cohere", "dimensions": 1024},
                {"name": "embed-multilingual-v3.0", "provider": "cohere", "dimensions": 1024},
            ])
        # Always available
        models.extend([
            {"name": "mock-embedding", "provider": "local", "dimensions": 1536},
        ])
        return models
