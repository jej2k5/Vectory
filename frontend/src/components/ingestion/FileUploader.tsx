"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileText, X, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUploadFile } from "@/hooks/useIngestion"
import { formatBytes } from "@/lib/utils"
import { showToast } from "@/hooks/useToast"

interface FileUploaderProps {
  collectionId: string
  onUploadComplete: (filePath: string, fileName: string, fileSize: number) => void
}

export function FileUploader({ collectionId, onUploadComplete }: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState("")
  const uploadMutation = useUploadFile()

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: unknown[]) => {
    setError("")
    if (rejectedFiles.length > 0) {
      setError("File type not supported or exceeds 100MB limit")
      return
    }
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
      "text/csv": [".csv"],
      "application/json": [".json"],
      "text/markdown": [".md"],
    },
    maxFiles: 1,
    maxSize: 100 * 1024 * 1024,
  })

  const handleUpload = async () => {
    if (!selectedFile) return
    setError("")

    try {
      const result = await uploadMutation.mutateAsync({
        file: selectedFile,
        collectionId,
      })
      showToast({
        title: "File uploaded",
        description: `${selectedFile.name} is ready for ingestion`,
        variant: "success",
      })
      onUploadComplete(result.file_path, result.file_name, result.file_size)
      setSelectedFile(null)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      const msg = axiosErr.response?.data?.detail || "Upload failed"
      setError(msg)
      showToast({ title: "Upload failed", description: msg, variant: "destructive" })
    }
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
        <p className="text-sm font-medium">
          {isDragActive ? "Drop the file here..." : "Drag & drop a file, or click to browse"}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          PDF, DOCX, TXT, CSV, JSON, MD (max 100MB)
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {selectedFile && (
        <div className="flex items-center justify-between p-3 border rounded-md">
          <div className="flex items-center space-x-3 min-w-0">
            <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">{formatBytes(selectedFile.size)}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 flex-shrink-0">
            <Button size="sm" onClick={handleUpload} disabled={uploadMutation.isPending}>
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setSelectedFile(null)
                setError("")
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
