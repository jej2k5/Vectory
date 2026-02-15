"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useCreateCollection } from "@/hooks/useCollections"
import { showToast } from "@/hooks/useToast"

interface CollectionFormProps {
  onSuccess?: () => void
}

export function CollectionForm({ onSuccess }: CollectionFormProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [embeddingModel, setEmbeddingModel] = useState("text-embedding-3-small")
  const [dimension, setDimension] = useState(1536)
  const [distanceMetric, setDistanceMetric] = useState("cosine")
  const [error, setError] = useState("")

  const createMutation = useCreateCollection()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    try {
      await createMutation.mutateAsync({
        name,
        description: description || undefined,
        embedding_model: embeddingModel,
        dimension,
        distance_metric: distanceMetric,
      })
      showToast({
        title: "Collection created",
        description: `"${name}" is ready for use`,
        variant: "success",
      })
      onSuccess?.()
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      const msg = axiosErr.response?.data?.detail || "Failed to create collection"
      setError(msg)
      showToast({ title: "Error", description: msg, variant: "destructive" })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
          {error}
        </div>
      )}
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="model">Embedding Model</Label>
          <select
            id="model"
            value={embeddingModel}
            onChange={(e) => setEmbeddingModel(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
            onChange={(e) => setDimension(parseInt(e.target.value) || 0)}
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
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
