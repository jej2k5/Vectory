// User types
export interface User {
  id: string;
  email: string;
  name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Collection types
export interface Collection {
  id: string;
  name: string;
  description: string | null;
  embedding_model: string;
  dimension: number;
  distance_metric: 'cosine' | 'euclidean' | 'dot_product';
  index_type: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  config: Record<string, any>;
  vector_count: number;
  index_size_bytes: number;
}

export interface CollectionCreate {
  name: string;
  description?: string;
  embedding_model: string;
  dimension: number;
  distance_metric?: string;
  index_type?: string;
  config?: Record<string, any>;
}

export interface CollectionStats {
  vector_count: number;
  total_queries: number;
  avg_latency_ms: number;
  index_type: string;
  distance_metric: string;
  created_at: string;
  index_size_bytes: number;
}

// Vector types
export interface VectorResult {
  id: string;
  collection_id: string;
  metadata: Record<string, any>;
  text_content: string | null;
  source_file: string | null;
  chunk_index: number | null;
  created_at: string;
  score?: number;
}

export interface QueryRequest {
  vector?: number[];
  text?: string;
  top_k?: number;
  filters?: Record<string, any>;
  distance_metric?: string;
  include_vectors?: boolean;
}

export interface QueryResponse {
  results: VectorResult[];
  total: number;
  latency_ms: number;
}

// Ingestion types
export interface IngestionJob {
  id: string;
  collection_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  file_path: string;
  file_name: string;
  file_size: number | null;
  file_type: string | null;
  total_chunks: number;
  processed_chunks: number;
  failed_chunks: number;
  error_message: string | null;
  config: Record<string, any>;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

// API Key types
export interface ApiKey {
  id: string;
  name: string;
  user_id: string;
  permissions: Record<string, any>;
  rate_limit: number;
  last_used_at: string | null;
  created_at: string;
  expires_at: string | null;
  is_active: boolean;
}

export interface ApiKeyCreateResponse extends ApiKey {
  raw_key: string;
}

// System types
export interface SystemHealth {
  status: string;
  database: string;
  redis: string;
  version: string;
}

export interface SystemMetrics {
  total_collections: number;
  total_vectors: number;
  total_queries: number;
  avg_latency_ms: number;
}

export interface EmbeddingModel {
  name: string;
  provider: string;
  dimensions: number;
}

// Pipeline template
export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  config: Record<string, any>;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}
