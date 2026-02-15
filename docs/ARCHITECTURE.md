# Vectory Architecture

## System Overview

```
                    +------------------+
                    |   Next.js        |
                    |   Dashboard      |
                    |   (Port 3000)    |
                    +--------+---------+
                             |
                             | HTTP/REST
                             v
                    +------------------+
                    |   FastAPI        |
                    |   Backend        |
                    |   (Port 8000)    |
                    +--+------+----+---+
                       |      |    |
            +----------+  +---+    +----------+
            |             |                   |
            v             v                   v
    +-------+------+  +---+------+    +-------+------+
    |  PostgreSQL   |  |  Redis   |    |   MinIO      |
    |  + pgvector   |  |  Queue   |    |   Storage    |
    |  (Port 5432)  |  |  (6379)  |    |  (9000/9001) |
    +---------------+  +---+------+    +--------------+
                           |
                           v
                    +------+-------+
                    | Celery Worker |
                    | (Background)  |
                    +--------------+
```

## Components

### Backend (FastAPI)
- RESTful API with OpenAPI documentation
- Async request handling with uvicorn
- JWT authentication + API key support
- Vector operations using pgvector SQL operators
- Pydantic v2 request/response validation

### Frontend (Next.js 14)
- App Router with server/client components
- TailwindCSS + shadcn/ui components
- React Query for data fetching
- Recharts for data visualization
- Responsive dashboard layout

### Database (PostgreSQL + pgvector)
- Vector storage with pgvector extension
- IVFFlat/HNSW indexes for fast similarity search
- JSONB metadata with GIN indexes
- Full-text search with tsvector indexes
- Automatic triggers for vector count tracking

### Redis
- Celery message broker
- Task result backend
- Future: query caching layer

### MinIO
- S3-compatible object storage
- Document file uploads
- Scalable file management

### Celery Workers
- Async document processing
- Text chunking and embedding generation
- Progress tracking via database updates

## Data Flows

### Vector Insertion
```
Client -> POST /api/collections/:id/vectors
       -> Validate dimension matches collection
       -> Generate fingerprint (SHA-256)
       -> INSERT into vectors table (pgvector)
       -> Return vector ID
```

### Similarity Search
```
Client -> POST /api/collections/:id/query
       -> Validate query vector dimension
       -> Execute pgvector distance query (<=>, <->, <#>)
       -> Apply metadata filters (JSONB @>)
       -> Record query analytics
       -> Return ranked results with scores
```

### Ingestion Pipeline
```
Client -> POST /api/ingestion/upload (file)
       -> Save to uploads directory
       -> POST /api/ingestion/jobs (create job)
       -> Dispatch Celery task
       -> Worker: Parse document (PDF/DOCX/TXT/CSV/JSON/MD)
       -> Worker: Chunk text (fixed_size/sentence/paragraph)
       -> Worker: Generate embeddings (OpenAI/mock)
       -> Worker: Batch INSERT vectors
       -> Worker: Update job progress
       -> Client polls: GET /api/ingestion/jobs/:id/progress (SSE)
```

## Database Schema

### Tables
- **users** - User accounts with bcrypt password hashes
- **collections** - Vector collection metadata and configuration
- **vectors** - Vector embeddings with pgvector type, JSONB metadata
- **ingestion_jobs** - File processing job tracking
- **api_keys** - API key hashes with permission scopes
- **queries** - Query analytics and latency tracking

### Key Indexes
- IVFFlat indexes on vectors for cosine, L2, and inner product
- GIN index on metadata JSONB for filter queries
- GIN index on text_content for full-text search
- B-tree indexes on foreign keys and timestamps

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| API Framework | FastAPI | Async, OpenAPI docs, Pydantic integration |
| Database | PostgreSQL + pgvector | Mature, ACID, native vector support |
| Frontend | Next.js 14 | App Router, SSR, React ecosystem |
| Task Queue | Celery + Redis | Battle-tested async processing |
| Auth | JWT + bcrypt | Stateless, industry standard |
| File Storage | MinIO | S3-compatible, self-hosted |

## Scalability

- **Connection pooling**: SQLAlchemy async pool (20 connections)
- **Batch operations**: Bulk vector insertion (1000+ per batch)
- **Index optimization**: IVFFlat with configurable list count
- **Async processing**: Celery workers for non-blocking ingestion
- **Horizontal scaling**: Multiple Celery workers, read replicas
