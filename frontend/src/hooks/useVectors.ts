"use client"

import { useMutation, useQuery } from "@tanstack/react-query"
import { vectorsApi } from "@/lib/api"
import type { QueryRequest } from "@/types"

export function useCollectionVectors(collectionId: string, skip = 0, limit = 50) {
  return useQuery({
    queryKey: ["collection-vectors", collectionId, skip, limit],
    queryFn: () => vectorsApi.list(collectionId, skip, limit),
    enabled: !!collectionId,
  })
}

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

export function useUpdateVector(collectionId: string) {
  return useMutation({
    mutationFn: ({
      vectorId,
      data,
    }: {
      vectorId: string
      data: { metadata?: Record<string, any>; text_content?: string }
    }) => vectorsApi.update(collectionId, vectorId, data),
  })
}

export function useDeleteVector(collectionId: string) {
  return useMutation({
    mutationFn: (vectorId: string) => vectorsApi.delete(collectionId, vectorId),
  })
}
