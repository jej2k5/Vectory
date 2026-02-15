# Vectory - Open Source Vector Database

A high-performance, self-hosted vector database with built-in ingestion pipelines for AI applications.

## Features

- **Vector Storage & Search**: Store and query high-dimensional embeddings with multiple distance metrics
- **Ingestion Pipelines**: Automated document processing (PDF, DOCX, TXT, CSV) with configurable chunking
- **Multi-Provider Embeddings**: Support for OpenAI, Anthropic, Cohere, and local models
- **Hybrid Search**: Combine vector similarity with metadata filtering
- **Admin Dashboard**: Modern web UI for managing collections and monitoring jobs
- **Developer-Friendly API**: RESTful API with Python and JavaScript SDKs
- **Self-Hostable**: Docker-based deployment with PostgreSQL + pgvector
- **Open Source**: MIT License

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) OpenAI/Anthropic API key for cloud embeddings

### Running with Docker

```bash
git clone https://github.com/jej2k5/vectory.git
cd vectory
cp .env.example .env
# Edit .env with your API keys (optional)
docker-compose up -d
```

Access at:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Project Structure

```
vectory/
├── backend/          # FastAPI backend
├── frontend/         # Next.js dashboard
├── database/         # PostgreSQL schemas
├── docker-compose.yml
└── README.md
```

## Documentation

- [API Reference](./docs/API.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Getting Started Guide](./docs/GETTING_STARTED.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

## Use Cases

- **Semantic Search**: Build intelligent search for documents, products, or content
- **RAG Applications**: Retrieval-augmented generation for chatbots and assistants
- **Recommendation Systems**: Find similar items based on embedding similarity
- **Content Deduplication**: Identify duplicate or near-duplicate content
- **Question Answering**: FAQ systems with semantic matching

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](./LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/vectory/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/vectory/discussions)
- **Documentation**: [docs/](./docs/)
