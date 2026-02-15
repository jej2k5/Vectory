"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatBytes, formatDuration } from "@/lib/utils"
import type { CollectionStats as Stats } from "@/types"

interface CollectionStatsProps {
  stats: Stats
}

export function CollectionStats({ stats }: CollectionStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Vectors</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{stats.vector_count.toLocaleString()}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Total Queries</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{stats.total_queries.toLocaleString()}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Avg Latency</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{formatDuration(stats.avg_latency_ms || 0)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Index Size</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{formatBytes(stats.index_size_bytes)}</p>
        </CardContent>
      </Card>
    </div>
  )
}
