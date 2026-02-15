"""Vector operations using NumPy."""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def euclidean_distance(a: list[float], b: list[float]) -> float:
    """Compute Euclidean distance between two vectors."""
    return float(np.linalg.norm(np.array(a) - np.array(b)))


def dot_product(a: list[float], b: list[float]) -> float:
    """Compute dot product of two vectors."""
    return float(np.dot(np.array(a), np.array(b)))


def normalize_vector(v: list[float]) -> list[float]:
    """Normalize a vector to unit length."""
    arr = np.array(v)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return v
    return (arr / norm).tolist()


def validate_vector_dimension(vector: list[float], expected_dim: int) -> bool:
    """Check if vector has the expected dimension."""
    return len(vector) == expected_dim
