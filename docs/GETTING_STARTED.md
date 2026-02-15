# Getting Started with Vectory

## Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **Git**
- (Optional) **OpenAI API key** for cloud embeddings

## Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/vectory.git
cd vectory

# Copy environment file
cp .env.example .env

# (Optional) Add your OpenAI API key to .env
# OPENAI_API_KEY=sk-...

# Start all services
docker-compose up -d

# Check that services are running
docker-compose ps
```

Access:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (via Docker)
docker-compose up -d postgres redis minio

# Run the backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## Your First Collection

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vectory.dev", "password": "password123", "name": "Admin"}'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@vectory.dev", "password": "password123"}'
```

Save the `access_token` from the response.

### 3. Create a Collection

```bash
curl -X POST http://localhost:8000/api/collections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "my-docs",
    "description": "My document collection",
    "embedding_model": "text-embedding-3-small",
    "dimension": 1536,
    "distance_metric": "cosine"
  }'
```

### 4. Insert Vectors

```bash
curl -X POST http://localhost:8000/api/collections/COLLECTION_ID/vectors \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "metadata": {"category": "docs"},
    "text_content": "This is a sample document."
  }'
```

### 5. Search

```bash
curl -X POST http://localhost:8000/api/collections/COLLECTION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],
    "top_k": 5
  }'
```

## Using the Ingestion Pipeline

### 1. Upload a Document

```bash
curl -X POST http://localhost:8000/api/ingestion/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@document.pdf" \
  -F "collection_id=COLLECTION_ID"
```

### 2. Create an Ingestion Job

```bash
curl -X POST "http://localhost:8000/api/ingestion/jobs?collection_id=COLLECTION_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "file_path": "/app/uploads/FILE_PATH",
    "file_name": "document.pdf",
    "file_size": 102400,
    "file_type": "pdf",
    "config": {
      "chunking_strategy": "sentence",
      "chunk_size": 500,
      "chunk_overlap": 50
    }
  }'
```

### 3. Monitor Progress

```bash
curl http://localhost:8000/api/ingestion/jobs/JOB_ID
```

## Using the Dashboard

1. Navigate to http://localhost:3000
2. Register or login
3. Create a collection from the Collections page
4. Click on a collection to:
   - Run queries in the Query Playground
   - Upload documents in the Ingest tab
   - View statistics in the Overview tab
5. Monitor ingestion jobs from the Ingestion page
6. Manage API keys from Settings

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Troubleshooting

**Database connection error:**
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Check the DATABASE_URL in your .env file

**Redis connection error:**
- Ensure Redis is running: `docker-compose ps redis`
- Check the REDIS_URL in your .env file

**Celery workers not processing:**
- Check worker logs: `docker-compose logs celery-worker`
- Ensure Redis is accessible from the worker

**Frontend can't reach backend:**
- Verify NEXT_PUBLIC_API_URL is set correctly
- Check CORS_ORIGINS includes the frontend URL

**Vector dimension mismatch:**
- Ensure your vectors match the collection's configured dimension
- Check with: `GET /api/collections/:id`
