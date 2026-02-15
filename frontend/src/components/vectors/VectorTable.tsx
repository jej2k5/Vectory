"use client"

import { useState } from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { truncate, formatDate } from "@/lib/utils"
import type { VectorResult } from "@/types"

interface VectorTableProps {
  vectors: VectorResult[]
  total: number
  page: number
  onPageChange: (page: number) => void
}

export function VectorTable({ vectors, total, page, onPageChange }: VectorTableProps) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const pageSize = 10
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div>
      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-3 text-left w-8"></th>
              <th className="p-3 text-left">ID</th>
              <th className="p-3 text-left">Text Content</th>
              <th className="p-3 text-left">Source</th>
              <th className="p-3 text-left">Score</th>
              <th className="p-3 text-left">Created</th>
            </tr>
          </thead>
          <tbody>
            {vectors.map((v) => (
              <>
                <tr
                  key={v.id}
                  className="border-b hover:bg-muted/30 cursor-pointer"
                  onClick={() => setExpanded(expanded === v.id ? null : v.id)}
                >
                  <td className="p-3">
                    {expanded === v.id ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </td>
                  <td className="p-3 font-mono text-xs">{truncate(v.id, 12)}</td>
                  <td className="p-3">{v.text_content ? truncate(v.text_content, 60) : "-"}</td>
                  <td className="p-3 text-xs">{v.source_file || "-"}</td>
                  <td className="p-3 font-medium">
                    {v.score !== undefined ? v.score.toFixed(4) : "-"}
                  </td>
                  <td className="p-3 text-xs">{formatDate(v.created_at)}</td>
                </tr>
                {expanded === v.id && (
                  <tr key={`${v.id}-detail`} className="border-b bg-muted/20">
                    <td colSpan={6} className="p-4">
                      <pre className="text-xs overflow-auto max-h-40 bg-muted p-3 rounded">
                        {JSON.stringify(v.metadata, null, 2)}
                      </pre>
                      {v.text_content && (
                        <div className="mt-2">
                          <p className="text-xs font-medium mb-1">Full Text:</p>
                          <p className="text-xs text-muted-foreground">{v.text_content}</p>
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
            {vectors.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-muted-foreground">
                  No vectors found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-muted-foreground">
            Showing {vectors.length} of {total} results
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
