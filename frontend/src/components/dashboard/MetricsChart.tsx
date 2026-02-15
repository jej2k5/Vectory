"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

interface MetricsChartProps {
  data: { date: string; queries: number; latency: number }[]
}

export function MetricsChart({ data }: MetricsChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" fontSize={12} />
        <YAxis fontSize={12} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="queries"
          stroke="hsl(222.2, 47.4%, 11.2%)"
          strokeWidth={2}
          name="Queries"
        />
        <Line
          type="monotone"
          dataKey="latency"
          stroke="hsl(0, 84.2%, 60.2%)"
          strokeWidth={2}
          name="Avg Latency (ms)"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
