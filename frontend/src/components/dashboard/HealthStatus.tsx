"use client"

import { useQuery } from "@tanstack/react-query"
import { systemApi } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function HealthStatus() {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => systemApi.health(),
    refetchInterval: 30000,
  })

  const statusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-500"
      case "degraded":
        return "bg-yellow-500"
      default:
        return "bg-red-500"
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">System Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm">API</span>
          <div className="flex items-center space-x-2">
            <div className={`h-2 w-2 rounded-full ${health ? "bg-green-500" : "bg-red-500"}`} />
            <span className="text-xs text-muted-foreground">{health ? "Online" : "Offline"}</span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Database</span>
          <div className="flex items-center space-x-2">
            <div
              className={`h-2 w-2 rounded-full ${statusColor(health?.database || "unknown")}`}
            />
            <span className="text-xs text-muted-foreground">
              {health?.database || "Unknown"}
            </span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Redis</span>
          <div className="flex items-center space-x-2">
            <div
              className={`h-2 w-2 rounded-full ${statusColor(health?.redis || "unknown")}`}
            />
            <span className="text-xs text-muted-foreground">{health?.redis || "Unknown"}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
