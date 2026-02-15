"use client"

import { useState } from "react"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { JobMonitor } from "@/components/ingestion/JobMonitor"
import { useIngestionJobs } from "@/hooks/useIngestion"
import { Upload } from "lucide-react"

export default function IngestionPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const { data, isLoading } = useIngestionJobs(undefined, statusFilter)

  const statuses = ["pending", "processing", "completed", "failed", "cancelled"]

  return (
    <DashboardLayout title="Ingestion Jobs">
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <Badge
            variant={!statusFilter ? "default" : "outline"}
            className="cursor-pointer"
            onClick={() => setStatusFilter(undefined)}
          >
            All
          </Badge>
          {statuses.map((s) => (
            <Badge
              key={s}
              variant={statusFilter === s ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setStatusFilter(s)}
            >
              {s}
            </Badge>
          ))}
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="h-24 animate-pulse bg-muted" />
            ))}
          </div>
        ) : data && data.items.length > 0 ? (
          <div className="space-y-3">
            {data.items.map((job) => (
              <JobMonitor key={job.id} job={job} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Upload className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No ingestion jobs</h3>
              <p className="text-sm text-muted-foreground">
                Upload documents to a collection to start ingesting
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
