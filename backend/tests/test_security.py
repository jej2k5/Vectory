"""Tests for security utilities."""
import pytest
from datetime import timedelta
from uuid import uuid4

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_api_key,
    hash_api_key,
)


class TestPasswordHashing:
    def test_hash_password(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert hashed.startswith("$2")

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2  # Different salts


class TestJWTTokens:
    def test_create_access_token(self):
        user_id = uuid4()
        token = create_access_token(subject=user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        user_id = uuid4()
        token = create_access_token(subject=user_id)
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        user_id = uuid4()
        token = create_refresh_token(subject=user_id)
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        user_id = uuid4()
        token = create_refresh_token(subject=user_id)
        payload = decode_refresh_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_access_token_cannot_be_decoded_as_refresh(self):
        token = create_access_token(subject=uuid4())
        with pytest.raises(Exception):
            decode_refresh_token(token)

    def test_refresh_token_cannot_be_decoded_as_access(self):
        token = create_refresh_token(subject=uuid4())
        with pytest.raises(Exception):
            decode_access_token(token)

    def test_custom_expiry(self):
        token = create_access_token(
            subject=uuid4(), expires_delta=timedelta(minutes=5)
        )
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_extra_claims(self):
        token = create_access_token(
            subject=uuid4(), extra_claims={"role": "admin"}
        )
        payload = decode_access_token(token)
        assert payload["role"] == "admin"


class TestApiKeys:
    def test_generate_api_key(self):
        key = generate_api_key()
        assert key.startswith("vy_")
        assert len(key) > 10

    def test_generate_unique_keys(self):
        key1 = generate_api_key()
        key2 = generate_api_key()
        assert key1 != key2

    def test_hash_api_key(self):
        key = generate_api_key()
        hashed = hash_api_key(key)
        assert hashed != key
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_hash_api_key_deterministic(self):
        key = "vy_test123"
        h1 = hash_api_key(key)
        h2 = hash_api_key(key)
        assert h1 == h2
