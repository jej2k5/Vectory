"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { collectionsApi } from "@/lib/api"
import type { CollectionCreate } from "@/types"

export function useCollections(skip = 0, limit = 50) {
  return useQuery({
    queryKey: ["collections", skip, limit],
    queryFn: () => collectionsApi.list(skip, limit),
  })
}

export function useCollection(id: string) {
  return useQuery({
    queryKey: ["collection", id],
    queryFn: () => collectionsApi.get(id),
    enabled: !!id,
  })
}

export function useCollectionStats(id: string) {
  return useQuery({
    queryKey: ["collection-stats", id],
    queryFn: () => collectionsApi.getStats(id),
    enabled: !!id,
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CollectionCreate) => collectionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] })
    },
  })
}

export function useUpdateCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CollectionCreate> }) =>
      collectionsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["collections"] })
      queryClient.invalidateQueries({ queryKey: ["collection", variables.id] })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => collectionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["collections"] })
    },
  })
}
