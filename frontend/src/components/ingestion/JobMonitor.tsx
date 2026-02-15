"use client"

import { RefreshCw, XCircle, Clock, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatBytes, formatDate } from "@/lib/utils"
import { useCancelJob, useRetryJob } from "@/hooks/useIngestion"
import type { IngestionJob } from "@/types"

interface JobMonitorProps {
  job: IngestionJob
}

const statusVariant = (status: string) => {
  switch (status) {
    case "completed": return "success" as const
    case "failed": return "destructive" as const
    case "processing": return "default" as const
    case "pending": return "warning" as const
    case "cancelled": return "secondary" as const
    default: return "outline" as const
  }
}

export function JobMonitor({ job }: JobMonitorProps) {
  const cancelMutation = useCancelJob()
  const retryMutation = useRetryJob()

  const progressPct =
    job.total_chunks > 0 ? Math.round((job.processed_chunks / job.total_chunks) * 100) : 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center space-x-2">
            <FileText className="h-4 w-4" />
            <span>{job.file_name}</span>
          </CardTitle>
          <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {job.status === "processing" && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>
                {job.processed_chunks} / {job.total_chunks} chunks
              </span>
              <span>{progressPct}%</span>
            </div>
            <Progress value={progressPct} />
          </div>
        )}

        <div className="grid grid-cols-2 gap-2 text-sm">
          {job.file_size && (
            <div>
              <span className="text-muted-foreground">Size: </span>
              {formatBytes(job.file_size)}
            </div>
          )}
          {job.started_at && (
            <div>
              <span className="text-muted-foreground">Started: </span>
              {formatDate(job.started_at)}
            </div>
          )}
          {job.completed_at && (
            <div>
              <span className="text-muted-foreground">Completed: </span>
              {formatDate(job.completed_at)}
            </div>
          )}
          {job.failed_chunks > 0 && (
            <div className="text-destructive">
              <span>Failed chunks: </span>
              {job.failed_chunks}
            </div>
          )}
        </div>

        {job.error_message && (
          <div className="p-2 bg-destructive/10 rounded text-xs text-destructive">
            {job.error_message}
          </div>
        )}

        <div className="flex space-x-2">
          {(job.status === "pending" || job.status === "processing") && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => cancelMutation.mutate(job.id)}
              disabled={cancelMutation.isPending}
            >
              <XCircle className="h-3 w-3 mr-1" />
              Cancel
            </Button>
          )}
          {job.status === "failed" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => retryMutation.mutate(job.id)}
              disabled={retryMutation.isPending}
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
