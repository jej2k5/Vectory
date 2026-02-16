"""Embedding providers for generating vector representations of text."""

from __future__ import annotations

import hashlib
import time
from typing import Any, Callable, TypeVar

import numpy as np

from app.config import settings
from app.utils.logger import logger

T = TypeVar('T')

# OpenAI API batch limit to avoid exceeding API constraints
MAX_OPENAI_BATCH_SIZE = 2048


def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_attempts: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
) -> Callable[..., T]:
    """Retry a function with exponential backoff on failure.

    Args:
        func: Function to retry
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation

    Returns:
        Wrapped function with retry logic
    """
    def wrapper(*args, **kwargs) -> T:
        delay = initial_delay
        last_exception = None

        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == max_attempts - 1:
                    # Last attempt failed, re-raise
                    raise

                # Log the retry
                logger.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                # Wait with exponential backoff
                time.sleep(delay)
                delay = min(delay * exponential_base, max_delay)

        # Should never reach here, but just in case
        raise last_exception or Exception("Retry logic failed unexpectedly")

    return wrapper


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
        """Generate embedding using OpenAI API with retry logic."""
        def _call_api():
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(input=text, model=model)
            return response.data[0].embedding

        try:
            return retry_with_exponential_backoff(_call_api)()
        except Exception as e:
            logger.error("OpenAI embedding failed after retries: {}", e)
            raise

    @staticmethod
    def _openai_batch_embeddings(texts: list[str], model: str) -> list[list[float]]:
        """Generate batch embeddings using OpenAI API with retry logic and batch size limits.

        Automatically splits large batches into smaller sub-batches to respect OpenAI API limits.
        Each sub-batch is retried independently with exponential backoff on failure.
        """
        def _call_api_batch(batch_texts: list[str]) -> list[list[float]]:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(input=batch_texts, model=model)
            return [item.embedding for item in response.data]

        try:
            # If batch is within limits, process directly
            if len(texts) <= MAX_OPENAI_BATCH_SIZE:
                return retry_with_exponential_backoff(_call_api_batch)(texts)

            # Split into sub-batches and process each with retry logic
            all_embeddings = []
            for i in range(0, len(texts), MAX_OPENAI_BATCH_SIZE):
                batch = texts[i:i + MAX_OPENAI_BATCH_SIZE]
                logger.info(f"Processing batch {i // MAX_OPENAI_BATCH_SIZE + 1} of {len(texts) // MAX_OPENAI_BATCH_SIZE + 1}")
                batch_embeddings = retry_with_exponential_backoff(_call_api_batch)(batch)
                all_embeddings.extend(batch_embeddings)

            return all_embeddings
        except Exception as e:
            logger.error("OpenAI batch embedding failed after retries: {}", e)
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
