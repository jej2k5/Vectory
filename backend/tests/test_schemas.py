"""Tests for Pydantic schemas."""
import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas.auth import UserCreate, UserLogin, TokenResponse, TokenRefresh
from app.schemas.user import UserResponse
from app.schemas.collection import CollectionCreate, CollectionUpdate, CollectionResponse, CollectionList, CollectionStats
from app.schemas.vector import VectorCreate, VectorUpdate, VectorResponse
from app.schemas.search import QueryRequest, QueryResponse, SearchResult, HybridSearchRequest
from app.schemas.ingestion import IngestionJobCreate, IngestionJobResponse, IngestionJobUpdate
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse, ApiKeyUpdate


class TestUserSchemas:
    def test_user_create_valid(self):
        user = UserCreate(email="test@example.com", password="password123", name="Test User")
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.name == "Test User"

    def test_user_create_no_name(self):
        user = UserCreate(email="test@example.com", password="password123")
        assert user.name is None

    def test_user_create_short_password(self):
        with pytest.raises(Exception):
            UserCreate(email="test@example.com", password="short")

    def test_user_login(self):
        login = UserLogin(email="test@example.com", password="password123")
        assert login.email == "test@example.com"

    def test_token_response(self):
        token = TokenResponse(access_token="abc", refresh_token="def", token_type="bearer")
        assert token.access_token == "abc"
        assert token.token_type == "bearer"

    def test_user_response(self):
        user = UserResponse(
            id=uuid4(),
            email="test@example.com",
            name="Test",
            is_active=True,
            created_at=datetime.now(),
        )
        assert user.is_active is True


class TestCollectionSchemas:
    def test_collection_create_defaults(self):
        c = CollectionCreate(name="test-collection")
        assert c.embedding_model == "text-embedding-3-small"
        assert c.dimension == 1536
        assert c.distance_metric == "cosine"
        assert c.index_type == "hnsw"

    def test_collection_create_custom(self):
        c = CollectionCreate(
            name="custom",
            description="Test description",
            embedding_model="text-embedding-ada-002",
            dimension=768,
            distance_metric="euclidean",
            index_type="ivfflat",
        )
        assert c.dimension == 768
        assert c.distance_metric == "euclidean"

    def test_collection_create_invalid_metric(self):
        with pytest.raises(Exception):
            CollectionCreate(name="test", distance_metric="invalid")

    def test_collection_update_partial(self):
        u = CollectionUpdate(name="new-name")
        data = u.model_dump(exclude_unset=True)
        assert "name" in data
        assert "description" not in data

    def test_collection_list(self):
        cl = CollectionList(items=[], total=0, skip=0, limit=50)
        assert cl.total == 0

    def test_collection_stats(self):
        stats = CollectionStats(
            collection_id=uuid4(),
            vector_count=100,
            dimension=1536,
            distance_metric="cosine",
            index_type="hnsw",
        )
        assert stats.vector_count == 100


class TestVectorSchemas:
    def test_vector_create(self):
        v = VectorCreate(vector=[0.1, 0.2, 0.3], metadata={"key": "value"}, text_content="hello")
        assert len(v.vector) == 3
        assert v.metadata == {"key": "value"}

    def test_vector_create_minimal(self):
        v = VectorCreate(vector=[1.0, 2.0])
        assert v.metadata is None
        assert v.text_content is None

    def test_vector_update_partial(self):
        u = VectorUpdate(text_content="updated")
        data = u.model_dump(exclude_unset=True)
        assert "text_content" in data
        assert "vector" not in data


class TestSearchSchemas:
    def test_query_request_defaults(self):
        q = QueryRequest(vector=[0.1, 0.2])
        assert q.top_k == 10
        assert q.include_vectors is False

    def test_query_request_with_filters(self):
        q = QueryRequest(vector=[0.1], top_k=5, filters={"category": "test"})
        assert q.filters == {"category": "test"}

    def test_hybrid_search_request(self):
        h = HybridSearchRequest(text="hello", vector_weight=0.8, text_weight=0.2)
        assert h.vector_weight == 0.8

    def test_search_result(self):
        r = SearchResult(id=uuid4(), score=0.95, metadata={"key": "val"})
        assert r.score == 0.95

    def test_query_response(self):
        r = QueryResponse(
            results=[SearchResult(id=uuid4(), score=0.9)],
            total=1,
            latency_ms=5.2,
        )
        assert r.total == 1
        assert r.latency_ms == 5.2


class TestIngestionSchemas:
    def test_ingestion_job_create(self):
        j = IngestionJobCreate(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            file_size=1024,
            file_type="pdf",
        )
        assert j.file_name == "test.pdf"

    def test_ingestion_job_update(self):
        u = IngestionJobUpdate(status="completed", processed_chunks=10)
        assert u.status == "completed"


class TestApiKeySchemas:
    def test_api_key_create(self):
        k = ApiKeyCreate(name="test-key")
        assert k.name == "test-key"
        assert k.permissions is None

    def test_api_key_create_response(self):
        k = ApiKeyCreateResponse(
            id=uuid4(),
            name="test",
            user_id=uuid4(),
            rate_limit=100,
            is_active=True,
            created_at=datetime.now(),
            raw_key="vy_abc123",
        )
        assert k.raw_key == "vy_abc123"
