import axios from "axios"
import { getAccessToken, clearTokens } from "@/lib/auth"
import type { ApiKey, Collection, EmbeddingModel, IngestionJob, PaginatedResponse } from "@/types"

const api = axios.create({
  baseURL: "",
  headers: { "Content-Type": "application/json" },
})

// Attach auth token to every request
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearTokens()
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/auth")) {
        window.location.href = "/auth/login"
      }
    }
    return Promise.reject(error)
  },
)

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const authApi = {
  login: async (data: { email: string; password: string }) => {
    const res = await api.post("/api/auth/login", data)
    return res.data
  },

  register: async (data: { email: string; password: string; name?: string }) => {
    const res = await api.post("/api/auth/register", data)
    return res.data
  },
}

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------

export const collectionsApi = {
  list: async (skip = 0, limit = 50): Promise<PaginatedResponse<Collection>> => {
    const res = await api.get("/api/collections/", { params: { skip, limit } })
    return res.data
  },

  get: async (id: string) => {
    const res = await api.get(`/api/collections/${id}`)
    return res.data
  },

  getStats: async (id: string) => {
    const res = await api.get(`/api/collections/${id}/stats`)
    return res.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  create: async (data: any) => {
    const res = await api.post("/api/collections/", data)
    return res.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  update: async (id: string, data: any) => {
    const res = await api.patch(`/api/collections/${id}`, data)
    return res.data
  },

  delete: async (id: string) => {
    const res = await api.delete(`/api/collections/${id}`)
    return res.data
  },
}

// ---------------------------------------------------------------------------
// Vectors
// ---------------------------------------------------------------------------

export const vectorsApi = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  query: async (collectionId: string, data: any) => {
    const res = await api.post(`/api/collections/${collectionId}/query`, data)
    return res.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  hybridSearch: async (collectionId: string, data: any) => {
    const res = await api.post(`/api/collections/${collectionId}/hybrid-search`, data)
    return res.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  insert: async (collectionId: string, data: any) => {
    const res = await api.post(`/api/collections/${collectionId}/vectors`, data)
    return res.data
  },

  delete: async (collectionId: string, vectorId: string) => {
    const res = await api.delete(`/api/collections/${collectionId}/vectors/${vectorId}`)
    return res.data
  },
}

// ---------------------------------------------------------------------------
// Ingestion
// ---------------------------------------------------------------------------

export const ingestionApi = {
  upload: async (file: File, collectionId: string) => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("collection_id", collectionId)
    const res = await api.post("/api/ingestion/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    return res.data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  createJob: async (collectionId: string, data: any) => {
    const res = await api.post("/api/ingestion/jobs", data, {
      params: { collection_id: collectionId },
    })
    return res.data
  },

  listJobs: async (params?: { collection_id?: string; status_filter?: string }): Promise<PaginatedResponse<IngestionJob>> => {
    const res = await api.get("/api/ingestion/jobs", { params })
    return res.data
  },

  getJob: async (jobId: string) => {
    const res = await api.get(`/api/ingestion/jobs/${jobId}`)
    return res.data
  },

  cancelJob: async (jobId: string) => {
    const res = await api.delete(`/api/ingestion/jobs/${jobId}`)
    return res.data
  },

  retryJob: async (jobId: string) => {
    const res = await api.post(`/api/ingestion/jobs/${jobId}/retry`)
    return res.data
  },

  getTemplates: async () => {
    const res = await api.get("/api/ingestion/templates")
    return res.data
  },
}

// ---------------------------------------------------------------------------
// API Keys
// ---------------------------------------------------------------------------

export const keysApi = {
  list: async (): Promise<ApiKey[]> => {
    const res = await api.get("/api/keys/")
    return res.data
  },

  create: async (data: { name: string }) => {
    const res = await api.post("/api/keys/", data)
    return res.data
  },

  delete: async (id: string) => {
    const res = await api.delete(`/api/keys/${id}`)
    return res.data
  },
}

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

export const systemApi = {
  health: async () => {
    const res = await api.get("/api/system/health")
    return res.data
  },

  metrics: async () => {
    const res = await api.get("/api/system/metrics")
    return res.data
  },

  models: async (): Promise<EmbeddingModel[]> => {
    const res = await api.get("/api/system/models")
    return res.data
  },

  info: async () => {
    const res = await api.get("/api/system/info")
    return res.data
  },
}
