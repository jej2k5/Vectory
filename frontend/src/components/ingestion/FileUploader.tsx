"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileText, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUploadFile } from "@/hooks/useIngestion"
import { formatBytes } from "@/lib/utils"

interface FileUploaderProps {
  collectionId: string
  onUploadComplete: (filePath: string, fileName: string, fileSize: number) => void
}

export function FileUploader({ collectionId, onUploadComplete }: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const uploadMutation = useUploadFile()

  const onDrop = useCallback((acceptedFiles: File[]) => {
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

    const result = await uploadMutation.mutateAsync({
      file: selectedFile,
      collectionId,
    })

    onUploadComplete(result.file_path, result.file_name, result.file_size)
    setSelectedFile(null)
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
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

      {selectedFile && (
        <div className="flex items-center justify-between p-3 border rounded-md">
          <div className="flex items-center space-x-3">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">{formatBytes(selectedFile.size)}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              size="sm"
              onClick={handleUpload}
              disabled={uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedFile(null)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
