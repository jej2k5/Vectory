"""Tests for embedding provider."""
import pytest

from app.core.embeddings import EmbeddingProvider


class TestMockEmbeddings:
    def test_get_embedding(self):
        embedding = EmbeddingProvider.get_embedding("hello world", dimension=384)
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(v, float) for v in embedding)

    def test_embedding_is_normalized(self):
        embedding = EmbeddingProvider.get_embedding("test", dimension=128)
        norm = sum(v * v for v in embedding) ** 0.5
        assert abs(norm - 1.0) < 1e-5

    def test_deterministic(self):
        e1 = EmbeddingProvider.get_embedding("same text", dimension=128)
        e2 = EmbeddingProvider.get_embedding("same text", dimension=128)
        assert e1 == e2

    def test_different_texts_different_embeddings(self):
        e1 = EmbeddingProvider.get_embedding("hello", dimension=128)
        e2 = EmbeddingProvider.get_embedding("world", dimension=128)
        assert e1 != e2

    def test_batch_embeddings(self):
        texts = ["hello", "world", "test"]
        embeddings = EmbeddingProvider.get_batch_embeddings(texts, dimension=128)
        assert len(embeddings) == 3
        assert all(len(e) == 128 for e in embeddings)

    def test_get_available_models(self):
        models = EmbeddingProvider.get_available_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all("name" in m and "provider" in m and "dimensions" in m for m in models)
