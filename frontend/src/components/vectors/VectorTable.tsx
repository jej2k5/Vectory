"use client"

import React, { useState } from "react"
import { ChevronDown, ChevronRight, Pencil, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import { EditVectorDialog } from "@/components/vectors/EditVectorDialog"
import { useDeleteVector, useUpdateVector } from "@/hooks/useVectors"
import { showToast } from "@/hooks/useToast"
import { truncate, formatDate } from "@/lib/utils"
import type { VectorResult } from "@/types"

interface VectorTableProps {
  vectors: VectorResult[]
  total: number
  page: number
  onPageChange: (page: number) => void
  collectionId?: string
}

export function VectorTable({ vectors, total, page, onPageChange, collectionId }: VectorTableProps) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [editTarget, setEditTarget] = useState<VectorResult | null>(null)
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set())
  const [localUpdates, setLocalUpdates] = useState<Map<string, Partial<VectorResult>>>(new Map())

  const deleteMutation = useDeleteVector(collectionId || "")
  const updateMutation = useUpdateVector(collectionId || "")

  const pageSize = 10
  const visibleVectors = vectors.filter((v) => !deletedIds.has(v.id))
  const totalPages = Math.ceil(total / pageSize)
  const hasActions = !!collectionId

  const handleDelete = async () => {
    if (!deleteTargetId) return
    try {
      await deleteMutation.mutateAsync(deleteTargetId)
      setDeletedIds((prev) => new Set(prev).add(deleteTargetId))
      showToast({ title: "Vector deleted", variant: "success" })
    } catch {
      showToast({ title: "Error", description: "Failed to delete vector", variant: "destructive" })
    }
    setDeleteTargetId(null)
  }

  const handleEdit = async (data: { metadata?: Record<string, any>; text_content?: string }) => {
    if (!editTarget) return
    try {
      await updateMutation.mutateAsync({ vectorId: editTarget.id, data })
      setLocalUpdates((prev) => {
        const next = new Map(prev)
        next.set(editTarget.id, { ...prev.get(editTarget.id), ...data })
        return next
      })
      showToast({ title: "Vector updated", variant: "success" })
      setEditTarget(null)
    } catch {
      showToast({ title: "Error", description: "Failed to update vector", variant: "destructive" })
    }
  }

  const getDisplayVector = (v: VectorResult): VectorResult => {
    const overrides = localUpdates.get(v.id)
    return overrides ? { ...v, ...overrides } : v
  }

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
              {hasActions && <th className="p-3 text-left w-24">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {visibleVectors.map((raw) => {
              const v = getDisplayVector(raw)
              return (
                <React.Fragment key={v.id}>
                  <tr
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
                    {hasActions && (
                      <td className="p-3">
                        <div className="flex space-x-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditTarget(v)
                            }}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                            onClick={(e) => {
                              e.stopPropagation()
                              setDeleteTargetId(v.id)
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                  {expanded === v.id && (
                    <tr className="border-b bg-muted/20">
                      <td colSpan={hasActions ? 7 : 6} className="p-4">
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
                </React.Fragment>
              )
            })}
            {visibleVectors.length === 0 && (
              <tr>
                <td colSpan={hasActions ? 7 : 6} className="p-8 text-center text-muted-foreground">
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
            Showing {visibleVectors.length} of {total} results
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

      <ConfirmDialog
        open={deleteTargetId !== null}
        onOpenChange={(open) => { if (!open) setDeleteTargetId(null) }}
        title="Delete vector"
        description="Are you sure you want to delete this vector? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        loading={deleteMutation.isPending}
      />

      {editTarget && (
        <EditVectorDialog
          open={editTarget !== null}
          onOpenChange={(open) => { if (!open) setEditTarget(null) }}
          vector={editTarget}
          onSave={handleEdit}
          loading={updateMutation.isPending}
        />
      )}
    </div>
  )
}
