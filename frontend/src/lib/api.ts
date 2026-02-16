import axios from "axios"
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "@/lib/auth"
import type {
  ApiKey,
  ApiKeyCreateResponse,
  Collection,
  EmbeddingModel,
  IngestionJob,
  PaginatedResponse,
  User,
} from "@/types"

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

// Handle 401 responses with automatic token refresh
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token!)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/login") &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(api(originalRequest))
            },
            reject,
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearTokens()
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/auth")) {
          window.location.href = "/auth/login"
        }
        return Promise.reject(error)
      }

      try {
        const res = await axios.post("/api/auth/refresh", {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token: newRefresh } = res.data
        setTokens(access_token, newRefresh)
        processQueue(null, access_token)

        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearTokens()
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/auth")) {
          window.location.href = "/auth/login"
        }
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
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

  me: async (): Promise<User> => {
    const res = await api.get("/api/auth/me")
    return res.data
  },

  refresh: async (refreshToken: string) => {
    const res = await api.post("/api/auth/refresh", { refresh_token: refreshToken })
    return res.data
  },
}

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------

export const collectionsApi = {
  list: async (skip = 0, limit = 50): Promise<PaginatedResponse<Collection>> => {
    const res = await api.get("/api/collections", { params: { skip, limit } })
    return res.data
  },

  get: async (id: string): Promise<Collection> => {
    const res = await api.get(`/api/collections/${id}`)
    return res.data
  },

  getStats: async (id: string) => {
    const res = await api.get(`/api/collections/${id}/stats`)
    return res.data
  },

  create: async (data: {
    name: string
    description?: string
    embedding_model: string
    dimension: number
    distance_metric?: string
    index_type?: string
  }): Promise<Collection> => {
    const res = await api.post("/api/collections", data)
    return res.data
  },

  update: async (
    id: string,
    data: Partial<{ name: string; description: string }>,
  ): Promise<Collection> => {
    const res = await api.patch(`/api/collections/${id}`, data)
    return res.data
  },

  delete: async (id: string) => {
    const res = await api.delete(`/api/collections/${id}`)
    return res.data
  },

  optimize: async (id: string) => {
    const res = await api.post(`/api/collections/${id}/optimize`)
    return res.data
  },

  exportData: async (id: string) => {
    const res = await api.post(`/api/collections/${id}/export`)
    return res.data
  },
}

// ---------------------------------------------------------------------------
// Vectors
// ---------------------------------------------------------------------------

export const vectorsApi = {
  query: async (
    collectionId: string,
    data: {
      vector?: number[]
      text?: string
      top_k?: number
      filters?: Record<string, unknown>
    },
  ) => {
    const res = await api.post(`/api/collections/${collectionId}/query`, data)
    return res.data
  },

  hybridSearch: async (
    collectionId: string,
    data: {
      vector?: number[]
      text?: string
      top_k?: number
      vector_weight?: number
      text_weight?: number
    },
  ) => {
    const res = await api.post(`/api/collections/${collectionId}/hybrid-search`, data)
    return res.data
  },

  insert: async (
    collectionId: string,
    data: {
      vector: number[]
      metadata?: Record<string, unknown>
      text_content?: string
    },
  ) => {
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

  createJob: async (collectionId: string, data: Record<string, unknown>) => {
    const res = await api.post("/api/ingestion/jobs", data, {
      params: { collection_id: collectionId },
    })
    return res.data
  },

  listJobs: async (params?: {
    collection_id?: string
    status_filter?: string
  }): Promise<PaginatedResponse<IngestionJob>> => {
    const res = await api.get("/api/ingestion/jobs", { params })
    return res.data
  },

  getJob: async (jobId: string): Promise<IngestionJob> => {
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
    const res = await api.get("/api/keys")
    return res.data
  },

  create: async (data: { name: string }): Promise<ApiKeyCreateResponse> => {
    const res = await api.post("/api/keys", data)
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
