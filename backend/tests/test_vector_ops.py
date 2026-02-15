"""Tests for vector operations."""
import pytest
import math

from app.core.vector_ops import (
    cosine_similarity,
    euclidean_distance,
    dot_product,
    normalize_vector,
    validate_vector_dimension,
)


class TestCosineSimularity:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(cosine_similarity(a, b) - (-1.0)) < 1e-6

    def test_similar_vectors(self):
        a = [1.0, 1.0]
        b = [1.0, 0.9]
        sim = cosine_similarity(a, b)
        assert sim > 0.99

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 1.0]
        assert cosine_similarity(a, b) == 0.0


class TestEuclideanDistance:
    def test_same_point(self):
        v = [1.0, 2.0, 3.0]
        assert euclidean_distance(v, v) == 0.0

    def test_unit_distance(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert abs(euclidean_distance(a, b) - 1.0) < 1e-6

    def test_diagonal(self):
        a = [0.0, 0.0]
        b = [3.0, 4.0]
        assert abs(euclidean_distance(a, b) - 5.0) < 1e-6


class TestDotProduct:
    def test_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert dot_product(a, b) == 0.0

    def test_parallel(self):
        a = [2.0, 3.0]
        b = [4.0, 5.0]
        assert dot_product(a, b) == 23.0


class TestNormalizeVector:
    def test_normalize(self):
        v = [3.0, 4.0]
        normalized = normalize_vector(v)
        assert abs(normalized[0] - 0.6) < 1e-6
        assert abs(normalized[1] - 0.8) < 1e-6

    def test_normalize_unit_vector(self):
        v = [1.0, 0.0, 0.0]
        normalized = normalize_vector(v)
        assert abs(normalized[0] - 1.0) < 1e-6

    def test_normalize_zero_vector(self):
        v = [0.0, 0.0]
        normalized = normalize_vector(v)
        assert normalized == [0.0, 0.0]

    def test_normalized_has_unit_length(self):
        v = [1.0, 2.0, 3.0, 4.0]
        normalized = normalize_vector(v)
        length = sum(x * x for x in normalized) ** 0.5
        assert abs(length - 1.0) < 1e-6


class TestValidateDimension:
    def test_correct_dimension(self):
        assert validate_vector_dimension([1.0, 2.0, 3.0], 3) is True

    def test_wrong_dimension(self):
        assert validate_vector_dimension([1.0, 2.0], 3) is False

    def test_empty_vector(self):
        assert validate_vector_dimension([], 0) is True
