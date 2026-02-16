-- Vectory Database Schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Collections table
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    embedding_model VARCHAR(100) NOT NULL,
    dimension INTEGER NOT NULL CHECK (dimension >= 128 AND dimension <= 4096),
    distance_metric VARCHAR(20) NOT NULL DEFAULT 'cosine' CHECK (distance_metric IN ('cosine', 'euclidean', 'dot_product')),
    index_type VARCHAR(20) DEFAULT 'hnsw',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    config JSONB DEFAULT '{}'::jsonb,
    vector_count INTEGER DEFAULT 0,
    index_size_bytes BIGINT DEFAULT 0
);

CREATE INDEX idx_collections_name ON collections(name);
CREATE INDEX idx_collections_created_by ON collections(created_by);
CREATE INDEX idx_collections_embedding_model ON collections(embedding_model);

-- Vectors table
CREATE TABLE vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    vector vector(1536) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    text_content TEXT,
    source_file VARCHAR(500),
    chunk_index INTEGER,
    fingerprint VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vectors_collection ON vectors(collection_id);
CREATE INDEX idx_vectors_metadata ON vectors USING GIN (metadata);
CREATE INDEX idx_vectors_text_content ON vectors USING GIN (to_tsvector('english', text_content));
CREATE INDEX idx_vectors_fingerprint ON vectors(fingerprint);
CREATE INDEX idx_vectors_created_at ON vectors(created_at);

-- Vector similarity indexes
CREATE INDEX idx_vectors_vector_cosine ON vectors USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_vectors_vector_l2 ON vectors USING ivfflat (vector vector_l2_ops) WITH (lists = 100);
CREATE INDEX idx_vectors_vector_ip ON vectors USING ivfflat (vector vector_ip_ops) WITH (lists = 100);

-- Ingestion jobs table
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    failed_chunks INTEGER DEFAULT 0,
    error_message TEXT,
    config JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ingestion_jobs_collection ON ingestion_jobs(collection_id);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX idx_ingestion_jobs_created_at ON ingestion_jobs(created_at);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '{}'::jsonb,
    rate_limit INTEGER DEFAULT 100,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Query analytics table
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    query_vector vector(1536),
    query_text TEXT,
    results_count INTEGER,
    latency_ms FLOAT,
    filters JSONB,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_queries_collection ON queries(collection_id);
CREATE INDEX idx_queries_created_at ON queries(created_at);
CREATE INDEX idx_queries_api_key ON queries(api_key_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vectors_updated_at BEFORE UPDATE ON vectors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingestion_jobs_updated_at BEFORE UPDATE ON ingestion_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update collection vector count
CREATE OR REPLACE FUNCTION update_collection_vector_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE collections
        SET vector_count = vector_count + 1
        WHERE id = NEW.collection_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE collections
        SET vector_count = vector_count - 1
        WHERE id = OLD.collection_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Apply vector count trigger
CREATE TRIGGER update_vector_count_trigger
AFTER INSERT OR DELETE ON vectors
FOR EACH ROW EXECUTE FUNCTION update_collection_vector_count();

-- Helper function to enable/disable the vector count trigger during bulk operations
-- This improves performance for large ingestions by avoiding per-row trigger overhead
CREATE OR REPLACE FUNCTION set_vector_count_trigger_enabled(enabled BOOLEAN)
RETURNS void AS $$
BEGIN
    IF enabled THEN
        ALTER TABLE vectors ENABLE TRIGGER update_vector_count_trigger;
    ELSE
        ALTER TABLE vectors DISABLE TRIGGER update_vector_count_trigger;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Helper function to manually update vector count for a collection
-- Use this after bulk inserts with the trigger disabled
CREATE OR REPLACE FUNCTION refresh_collection_vector_count(p_collection_id UUID)
RETURNS void AS $$
BEGIN
    UPDATE collections
    SET vector_count = (
        SELECT COUNT(*)
        FROM vectors
        WHERE collection_id = p_collection_id
    )
    WHERE id = p_collection_id;
END;
$$ LANGUAGE plpgsql;
