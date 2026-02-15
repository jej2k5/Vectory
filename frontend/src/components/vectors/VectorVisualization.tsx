"use client"

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import type { VectorResult } from "@/types"

interface VectorVisualizationProps {
  results: VectorResult[]
}

export function VectorVisualization({ results }: VectorVisualizationProps) {
  const data = results.map((r, index) => ({
    index,
    score: r.score ?? 0,
    name: r.text_content ? r.text_content.slice(0, 30) : r.id.slice(0, 8),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="index" name="Result" fontSize={12} />
        <YAxis dataKey="score" name="Score" fontSize={12} />
        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
        <Scatter name="Results" data={data} fill="hsl(222.2, 47.4%, 11.2%)" />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
