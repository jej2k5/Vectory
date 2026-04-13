"use client"

import { useState, useEffect } from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import type { VectorResult } from "@/types"

interface EditVectorDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  vector: VectorResult
  onSave: (data: { metadata?: Record<string, any>; text_content?: string }) => void
  loading?: boolean
}

export function EditVectorDialog({
  open,
  onOpenChange,
  vector,
  onSave,
  loading = false,
}: EditVectorDialogProps) {
  const [textContent, setTextContent] = useState(vector.text_content || "")
  const [metadataStr, setMetadataStr] = useState(JSON.stringify(vector.metadata || {}, null, 2))
  const [metadataError, setMetadataError] = useState("")

  useEffect(() => {
    setTextContent(vector.text_content || "")
    setMetadataStr(JSON.stringify(vector.metadata || {}, null, 2))
    setMetadataError("")
  }, [vector])

  const handleSave = () => {
    let metadata: Record<string, any> | undefined
    if (metadataStr.trim()) {
      try {
        metadata = JSON.parse(metadataStr)
      } catch {
        setMetadataError("Invalid JSON")
        return
      }
    }
    setMetadataError("")
    onSave({
      text_content: textContent || undefined,
      metadata,
    })
  }

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogPrimitive.Content
          className={cn(
            "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-card p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
          )}
        >
          <div className="flex flex-col space-y-2">
            <DialogPrimitive.Title className="text-lg font-semibold">
              Edit Vector
            </DialogPrimitive.Title>
            <DialogPrimitive.Description className="text-sm text-muted-foreground">
              Update the text content or metadata for this vector.
            </DialogPrimitive.Description>
          </div>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Text Content</Label>
              <Textarea
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                rows={4}
                placeholder="Enter text content..."
              />
            </div>
            <div className="space-y-2">
              <Label>Metadata (JSON)</Label>
              <Textarea
                value={metadataStr}
                onChange={(e) => {
                  setMetadataStr(e.target.value)
                  setMetadataError("")
                }}
                rows={5}
                className="font-mono text-xs"
                placeholder="{}"
              />
              {metadataError && (
                <p className="text-xs text-destructive">{metadataError}</p>
              )}
            </div>
          </div>
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={loading}>
              {loading ? "Saving..." : "Save"}
            </Button>
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
