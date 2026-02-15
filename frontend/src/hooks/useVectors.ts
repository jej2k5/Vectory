"use client"

import { useMutation } from "@tanstack/react-query"
import { vectorsApi } from "@/lib/api"
import type { QueryRequest } from "@/types"

export function useVectorQuery(collectionId: string) {
  return useMutation({
    mutationFn: (data: QueryRequest) => vectorsApi.query(collectionId, data),
  })
}

export function useHybridSearch(collectionId: string) {
  return useMutation({
    mutationFn: (data: QueryRequest & { vector_weight?: number; text_weight?: number }) =>
      vectorsApi.hybridSearch(collectionId, data),
  })
}

export function useInsertVector(collectionId: string) {
  return useMutation({
    mutationFn: (data: { vector: number[]; metadata?: Record<string, any>; text_content?: string }) =>
      vectorsApi.insert(collectionId, data),
  })
}

export function useDeleteVector(collectionId: string) {
  return useMutation({
    mutationFn: (vectorId: string) => vectorsApi.delete(collectionId, vectorId),
  })
}
