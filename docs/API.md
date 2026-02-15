# Vectory API Reference

## Authentication

All authenticated endpoints require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Alternatively, use an API key via the `X-API-Key` header:

```
X-API-Key: vy_your_api_key_here
```

---

## Auth Endpoints

### POST /api/auth/register
Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

### POST /api/auth/login
Authenticate and obtain JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /api/auth/refresh
Refresh an expired access token.

**Request Body:**
```json
{
  "refresh_token": "eyJ..."
}
```

### GET /api/auth/me
Get the current user's profile. Requires authentication.

---

## Collections

### GET /api/collections
List all collections.

**Query Parameters:**
- `skip` (int, default: 0) - Number of items to skip
- `limit` (int, default: 50) - Maximum items to return

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "my-collection",
      "description": "Description",
      "embedding_model": "text-embedding-3-small",
      "dimension": 1536,
      "distance_metric": "cosine",
      "index_type": "hnsw",
      "vector_count": 1000,
      "index_size_bytes": 0,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /api/collections
Create a new collection. Requires authentication.

**Request Body:**
```json
{
  "name": "my-collection",
  "description": "A test collection",
  "embedding_model": "text-embedding-3-small",
  "dimension": 1536,
  "distance_metric": "cosine",
  "index_type": "hnsw"
}
```

### GET /api/collections/:id
Get collection details.

### PATCH /api/collections/:id
Update a collection. Requires authentication.

### DELETE /api/collections/:id
Delete a collection and all its vectors. Requires authentication.

### GET /api/collections/:id/stats
Get collection statistics including vector count, query count, and average latency.

### POST /api/collections/:id/optimize
Trigger index rebuild. Requires authentication.

### POST /api/collections/:id/export
Export all collection data as JSON.

---

## Vectors

### POST /api/collections/:id/vectors
Insert one or more vectors.

**Single vector:**
```json
{
  "vector": [0.1, 0.2, 0.3, ...],
  "metadata": {"category": "science"},
  "text_content": "Original text content",
  "source_file": "document.pdf",
  "chunk_index": 0
}
```

**Batch insert (array):**
```json
[
  {"vector": [0.1, ...], "text_content": "chunk 1"},
  {"vector": [0.2, ...], "text_content": "chunk 2"}
]
```

### GET /api/collections/:id/vectors/:vector_id
Get a specific vector by ID.

### PATCH /api/collections/:id/vectors/:vector_id
Update a vector. Requires authentication.

### DELETE /api/collections/:id/vectors/:vector_id
Delete a vector. Requires authentication.

### POST /api/collections/:id/vectors/batch-delete
Bulk delete vectors by IDs. Requires authentication.

### POST /api/collections/:id/query
Similarity search.

**Request Body:**
```json
{
  "vector": [0.1, 0.2, ...],
  "top_k": 10,
  "filters": {"category": "science"},
  "distance_metric": "cosine",
  "include_vectors": false
}
```

**Response (200):**
```json
{
  "results": [
    {
      "id": "uuid",
      "score": 0.95,
      "distance": 0.05,
      "metadata": {"category": "science"},
      "text_content": "Matching text"
    }
  ],
  "total": 10,
  "latency_ms": 12.5,
  "collection_id": "uuid",
  "distance_metric": "cosine"
}
```

### POST /api/collections/:id/hybrid-search
Combined vector + full-text search.

**Request Body:**
```json
{
  "text": "search query",
  "vector": [0.1, 0.2, ...],
  "top_k": 10,
  "vector_weight": 0.7,
  "text_weight": 0.3
}
```

---

## Ingestion

### POST /api/ingestion/upload
Upload a file for ingestion. Uses multipart/form-data.

**Form Fields:**
- `file` - The file to upload (PDF, DOCX, TXT, CSV, JSON, MD)
- `collection_id` - Target collection UUID

### POST /api/ingestion/jobs?collection_id=:id
Create an ingestion job.

**Request Body:**
```json
{
  "file_path": "/app/uploads/file.pdf",
  "file_name": "document.pdf",
  "file_size": 102400,
  "file_type": "pdf",
  "config": {
    "chunking_strategy": "sentence",
    "chunk_size": 500,
    "chunk_overlap": 50
  }
}
```

### GET /api/ingestion/jobs
List ingestion jobs. Supports filtering by `collection_id` and `status_filter`.

### GET /api/ingestion/jobs/:id
Get job details.

### GET /api/ingestion/jobs/:id/progress
Server-Sent Events endpoint for real-time progress updates.

### DELETE /api/ingestion/jobs/:id
Cancel a pending/processing job. Requires authentication.

### POST /api/ingestion/jobs/:id/retry
Retry a failed job. Requires authentication.

### GET /api/ingestion/templates
List available pipeline templates (RAG, Semantic Search, FAQ).

---

## API Keys

### GET /api/keys
List the current user's API keys. Requires authentication.

### POST /api/keys
Create a new API key. Requires authentication.

**Request Body:**
```json
{
  "name": "My API Key",
  "permissions": {},
  "expires_at": "2027-01-01T00:00:00Z"
}
```

**Response (201):** Includes `raw_key` field (shown only once).

### DELETE /api/keys/:id
Revoke an API key. Requires authentication.

### PATCH /api/keys/:id
Update API key name/permissions. Requires authentication.

---

## System

### GET /api/health
Health check. Returns database and Redis connectivity status.

### GET /api/metrics
System metrics: total collections, vectors, queries, and average latency.

### GET /api/models
List available embedding models with provider and dimension info.

### GET /api/system/info
System version and capabilities.

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error description"
}
```

Common status codes:
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Resource not found
- `409` - Conflict (duplicate resource)
- `500` - Internal server error
