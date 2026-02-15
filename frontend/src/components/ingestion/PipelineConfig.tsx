"use client"

import { useState } from "react"
import { Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useCreateIngestionJob } from "@/hooks/useIngestion"

interface PipelineConfigProps {
  collectionId: string
  filePath: string
  fileName: string
  fileSize: number
}

export function PipelineConfig({ collectionId, filePath, fileName, fileSize }: PipelineConfigProps) {
  const [chunkingStrategy, setChunkingStrategy] = useState("sentence")
  const [chunkSize, setChunkSize] = useState(500)
  const [chunkOverlap, setChunkOverlap] = useState(50)

  const createJob = useCreateIngestionJob()

  const handleStart = async () => {
    await createJob.mutateAsync({
      collectionId,
      data: {
        file_path: filePath,
        file_name: fileName,
        file_size: fileSize,
        file_type: fileName.split(".").pop() || "txt",
        config: {
          chunking_strategy: chunkingStrategy,
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap,
        },
      },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Pipeline Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Chunking Strategy</Label>
          <select
            value={chunkingStrategy}
            onChange={(e) => setChunkingStrategy(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="fixed_size">Fixed Size</option>
            <option value="sentence">Sentence</option>
            <option value="paragraph">Paragraph</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Chunk Size</Label>
            <Input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(parseInt(e.target.value))}
              min={100}
              max={2000}
            />
          </div>
          <div className="space-y-2">
            <Label>Chunk Overlap</Label>
            <Input
              type="number"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
              min={0}
              max={200}
            />
          </div>
        </div>
        <Button onClick={handleStart} disabled={createJob.isPending} className="w-full">
          <Play className="h-4 w-4 mr-2" />
          {createJob.isPending ? "Starting..." : "Start Ingestion"}
        </Button>
      </CardContent>
    </Card>
  )
}
