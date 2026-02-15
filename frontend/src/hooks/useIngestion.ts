"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { ingestionApi } from "@/lib/api"

export function useIngestionJobs(collectionId?: string, status?: string) {
  return useQuery({
    queryKey: ["ingestion-jobs", collectionId, status],
    queryFn: () =>
      ingestionApi.listJobs({
        collection_id: collectionId,
        status_filter: status,
      }),
  })
}

export function useIngestionJob(jobId: string) {
  return useQuery({
    queryKey: ["ingestion-job", jobId],
    queryFn: () => ingestionApi.getJob(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === "processing" || status === "pending" ? 2000 : false
    },
  })
}

export function useUploadFile() {
  return useMutation({
    mutationFn: ({ file, collectionId }: { file: File; collectionId: string }) =>
      ingestionApi.upload(file, collectionId),
  })
}

export function useCreateIngestionJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ collectionId, data }: { collectionId: string; data: any }) =>
      ingestionApi.createJob(collectionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ingestion-jobs"] })
    },
  })
}

export function useCancelJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) => ingestionApi.cancelJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ingestion-jobs"] })
    },
  })
}

export function useRetryJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) => ingestionApi.retryJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ingestion-jobs"] })
    },
  })
}

export function usePipelineTemplates() {
  return useQuery({
    queryKey: ["pipeline-templates"],
    queryFn: () => ingestionApi.getTemplates(),
  })
}
