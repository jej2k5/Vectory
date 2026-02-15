"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { Database, Search, Activity, Clock, Plus, ArrowRight } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { HealthStatus } from "@/components/dashboard/HealthStatus"
import { MetricsChart } from "@/components/dashboard/MetricsChart"
import { CollectionCard } from "@/components/collections/CollectionCard"
import { systemApi, collectionsApi } from "@/lib/api"

// Placeholder chart data (populated by metrics if available)
const defaultChartData = [
  { date: "Mon", queries: 0, latency: 0 },
  { date: "Tue", queries: 0, latency: 0 },
  { date: "Wed", queries: 0, latency: 0 },
  { date: "Thu", queries: 0, latency: 0 },
  { date: "Fri", queries: 0, latency: 0 },
  { date: "Sat", queries: 0, latency: 0 },
  { date: "Sun", queries: 0, latency: 0 },
]

export default function DashboardPage() {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["metrics"],
    queryFn: () => systemApi.metrics(),
  })

  const { data: collections, isLoading: collectionsLoading } = useQuery({
    queryKey: ["collections", 0, 6],
    queryFn: () => collectionsApi.list(0, 6),
  })

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-6">
        {/* Metrics cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Collections</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {metricsLoading ? (
                <div className="h-8 w-12 bg-muted rounded animate-pulse" />
              ) : (
                <div className="text-2xl font-bold">
                  {metrics?.total_collections ?? 0}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Vectors</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {metricsLoading ? (
                <div className="h-8 w-16 bg-muted rounded animate-pulse" />
              ) : (
                <div className="text-2xl font-bold">
                  {(metrics?.total_vectors ?? 0).toLocaleString()}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
              <Search className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {metricsLoading ? (
                <div className="h-8 w-16 bg-muted rounded animate-pulse" />
              ) : (
                <div className="text-2xl font-bold">
                  {(metrics?.total_queries ?? 0).toLocaleString()}
                </div>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {metricsLoading ? (
                <div className="h-8 w-16 bg-muted rounded animate-pulse" />
              ) : (
                <div className="text-2xl font-bold">
                  {(metrics?.avg_latency_ms ?? 0).toFixed(1)}ms
                </div>
              )}
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
              <MetricsChart data={defaultChartData} />
            </CardContent>
          </Card>
          <HealthStatus />
        </div>

        {/* Recent collections */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Collections</h2>
            <Link href="/collections">
              <Button variant="ghost" size="sm">
                View all
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </div>
          {collectionsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="h-48 animate-pulse bg-muted" />
              ))}
            </div>
          ) : collections && collections.items.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {collections.items.slice(0, 3).map((c) => (
                <CollectionCard key={c.id} collection={c} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-8">
                <Database className="h-10 w-10 text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground mb-3">
                  No collections yet. Create one to get started.
                </p>
                <Link href="/collections">
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-1" />
                    Create Collection
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
