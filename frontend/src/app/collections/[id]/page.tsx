"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CollectionStats } from "@/components/collections/CollectionStats"
import { QueryPlayground } from "@/components/query/QueryPlayground"
import { FileUploader } from "@/components/ingestion/FileUploader"
import { PipelineConfig } from "@/components/ingestion/PipelineConfig"
import { useCollection, useCollectionStats } from "@/hooks/useCollections"
import { useIngestionJobs } from "@/hooks/useIngestion"
import { JobMonitor } from "@/components/ingestion/JobMonitor"

export default function CollectionDetailPage() {
  const params = useParams()
  const collectionId = params.id as string
  const { data: collection, isLoading } = useCollection(collectionId)
  const { data: stats } = useCollectionStats(collectionId)
  const { data: jobs } = useIngestionJobs(collectionId)

  const [uploadedFile, setUploadedFile] = useState<{
    filePath: string
    fileName: string
    fileSize: number
  } | null>(null)

  if (isLoading || !collection) {
    return (
      <DashboardLayout title="Loading...">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3" />
          <div className="h-4 bg-muted rounded w-1/2" />
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title={collection.name}>
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Badge variant="secondary">{collection.distance_metric}</Badge>
          <Badge variant="outline">{collection.embedding_model}</Badge>
          <Badge variant="outline">{collection.dimension}d</Badge>
        </div>

        {collection.description && (
          <p className="text-muted-foreground">{collection.description}</p>
        )}

        {stats && <CollectionStats stats={stats} />}

        <Tabs defaultValue="query">
          <TabsList>
            <TabsTrigger value="query">Query</TabsTrigger>
            <TabsTrigger value="ingest">Ingest</TabsTrigger>
            <TabsTrigger value="overview">Overview</TabsTrigger>
          </TabsList>

          <TabsContent value="query" className="mt-4">
            <QueryPlayground collectionId={collectionId} />
          </TabsContent>

          <TabsContent value="ingest" className="mt-4 space-y-6">
            <FileUploader
              collectionId={collectionId}
              onUploadComplete={(filePath, fileName, fileSize) =>
                setUploadedFile({ filePath, fileName, fileSize })
              }
            />
            {uploadedFile && (
              <PipelineConfig
                collectionId={collectionId}
                filePath={uploadedFile.filePath}
                fileName={uploadedFile.fileName}
                fileSize={uploadedFile.fileSize}
              />
            )}
            {jobs && jobs.items.length > 0 && (
              <div className="space-y-3">
                <h3 className="font-semibold">Ingestion Jobs</h3>
                {jobs.items.map((job) => (
                  <JobMonitor key={job.id} job={job} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="overview" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle>Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                  {JSON.stringify(
                    {
                      id: collection.id,
                      name: collection.name,
                      embedding_model: collection.embedding_model,
                      dimension: collection.dimension,
                      distance_metric: collection.distance_metric,
                      index_type: collection.index_type,
                      config: collection.config,
                    },
                    null,
                    2
                  )}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}
