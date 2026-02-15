"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useCreateCollection } from "@/hooks/useCollections"

interface CollectionFormProps {
  onSuccess?: () => void
}

export function CollectionForm({ onSuccess }: CollectionFormProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [embeddingModel, setEmbeddingModel] = useState("text-embedding-3-small")
  const [dimension, setDimension] = useState(1536)
  const [distanceMetric, setDistanceMetric] = useState("cosine")

  const createMutation = useCreateCollection()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await createMutation.mutateAsync({
      name,
      description: description || undefined,
      embedding_model: embeddingModel,
      dimension,
      distance_metric: distanceMetric,
    })
    onSuccess?.()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-collection"
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Optional description..."
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="model">Embedding Model</Label>
          <select
            id="model"
            value={embeddingModel}
            onChange={(e) => setEmbeddingModel(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="text-embedding-3-small">text-embedding-3-small</option>
            <option value="text-embedding-3-large">text-embedding-3-large</option>
            <option value="text-embedding-ada-002">text-embedding-ada-002</option>
            <option value="all-MiniLM-L6-v2">all-MiniLM-L6-v2</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="dimension">Dimension</Label>
          <Input
            id="dimension"
            type="number"
            value={dimension}
            onChange={(e) => setDimension(parseInt(e.target.value))}
            min={128}
            max={4096}
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="metric">Distance Metric</Label>
        <select
          id="metric"
          value={distanceMetric}
          onChange={(e) => setDistanceMetric(e.target.value)}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="cosine">Cosine</option>
          <option value="euclidean">Euclidean</option>
          <option value="dot_product">Dot Product</option>
        </select>
      </div>
      <Button type="submit" disabled={createMutation.isPending} className="w-full">
        {createMutation.isPending ? "Creating..." : "Create Collection"}
      </Button>
    </form>
  )
}
