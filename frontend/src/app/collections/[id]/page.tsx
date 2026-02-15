"use client"

import { useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Trash2, AlertCircle } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import { CollectionStats } from "@/components/collections/CollectionStats"
import { QueryPlayground } from "@/components/query/QueryPlayground"
import { FileUploader } from "@/components/ingestion/FileUploader"
import { PipelineConfig } from "@/components/ingestion/PipelineConfig"
import { useCollection, useCollectionStats, useDeleteCollection } from "@/hooks/useCollections"
import { useIngestionJobs } from "@/hooks/useIngestion"
import { JobMonitor } from "@/components/ingestion/JobMonitor"
import { showToast } from "@/hooks/useToast"

export default function CollectionDetailPage() {
  const params = useParams()
  const router = useRouter()
  const collectionId = params.id as string
  const { data: collection, isLoading, error } = useCollection(collectionId)
  const { data: stats } = useCollectionStats(collectionId)
  const { data: jobs } = useIngestionJobs(collectionId)
  const deleteMutation = useDeleteCollection()

  const [uploadedFile, setUploadedFile] = useState<{
    filePath: string
    fileName: string
    fileSize: number
  } | null>(null)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(collectionId)
      showToast({
        title: "Collection deleted",
        description: `"${collection?.name}" has been removed`,
        variant: "success",
      })
      router.push("/collections")
    } catch {
      showToast({ title: "Error", description: "Failed to delete collection", variant: "destructive" })
    }
    setShowDeleteDialog(false)
  }

  if (error) {
    return (
      <DashboardLayout title="Error">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Collection not found</h3>
            <p className="text-sm text-muted-foreground mb-4">
              The collection may have been deleted or the ID is invalid.
            </p>
            <Button onClick={() => router.push("/collections")}>Back to Collections</Button>
          </CardContent>
        </Card>
      </DashboardLayout>
    )
  }

  if (isLoading || !collection) {
    return (
      <DashboardLayout title="Loading...">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3" />
          <div className="h-4 bg-muted rounded w-1/2" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-muted rounded" />
            ))}
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title={collection.name}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center space-x-2 flex-wrap gap-y-2">
            <Badge variant="secondary">{collection.distance_metric}</Badge>
            <Badge variant="outline">{collection.embedding_model}</Badge>
            <Badge variant="outline">{collection.dimension}d</Badge>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Delete
          </Button>
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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">ID</p>
                    <p className="font-mono text-xs break-all">{collection.id}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Name</p>
                    <p className="font-medium">{collection.name}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Embedding Model</p>
                    <p className="font-medium">{collection.embedding_model}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Dimension</p>
                    <p className="font-medium">{collection.dimension}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Distance Metric</p>
                    <p className="font-medium">{collection.distance_metric}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Index Type</p>
                    <p className="font-medium">{collection.index_type}</p>
                  </div>
                </div>
                {collection.config && Object.keys(collection.config).length > 0 && (
                  <div className="mt-4">
                    <p className="text-muted-foreground text-sm mb-2">Config</p>
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                      {JSON.stringify(collection.config, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete collection"
        description={`Are you sure you want to delete "${collection.name}"? This will permanently remove all vectors and data. This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        loading={deleteMutation.isPending}
      />
    </DashboardLayout>
  )
}
