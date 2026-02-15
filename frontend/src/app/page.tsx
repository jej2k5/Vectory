"use client"

import { useQuery } from "@tanstack/react-query"
import { Database, Search, Upload, Activity } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { HealthStatus } from "@/components/dashboard/HealthStatus"
import { MetricsChart } from "@/components/dashboard/MetricsChart"
import { CollectionCard } from "@/components/collections/CollectionCard"
import { systemApi, collectionsApi } from "@/lib/api"

// Mock chart data
const chartData = [
  { date: "Mon", queries: 120, latency: 12 },
  { date: "Tue", queries: 180, latency: 15 },
  { date: "Wed", queries: 250, latency: 10 },
  { date: "Thu", queries: 200, latency: 13 },
  { date: "Fri", queries: 310, latency: 11 },
  { date: "Sat", queries: 150, latency: 9 },
  { date: "Sun", queries: 90, latency: 8 },
]

export default function DashboardPage() {
  const { data: metrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: () => systemApi.metrics(),
  })

  const { data: collections } = useQuery({
    queryKey: ["collections", 0, 5],
    queryFn: () => collectionsApi.list(0, 5),
  })

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-6">
        {/* Metrics cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Collections</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics?.total_collections ?? 0}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Vectors</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(metrics?.total_vectors ?? 0).toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
              <Search className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(metrics?.total_queries ?? 0).toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
              <Upload className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(metrics?.avg_latency_ms ?? 0).toFixed(1)}ms
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chart and Health */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Query Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <MetricsChart data={chartData} />
            </CardContent>
          </Card>
          <HealthStatus />
        </div>

        {/* Recent collections */}
        {collections && collections.items.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Recent Collections</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {collections.items.slice(0, 3).map((c) => (
                <CollectionCard key={c.id} collection={c} />
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
