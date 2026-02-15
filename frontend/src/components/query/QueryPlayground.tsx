"use client"

import { useState } from "react"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useVectorQuery } from "@/hooks/useVectors"
import { ResultsView } from "./ResultsView"
import type { QueryResponse } from "@/types"

interface QueryPlaygroundProps {
  collectionId: string
}

export function QueryPlayground({ collectionId }: QueryPlaygroundProps) {
  const [queryText, setQueryText] = useState("")
  const [vectorInput, setVectorInput] = useState("")
  const [topK, setTopK] = useState(10)
  const [results, setResults] = useState<QueryResponse | null>(null)

  const queryMutation = useVectorQuery(collectionId)

  const handleSearch = async () => {
    let vector: number[] | undefined
    if (vectorInput.trim()) {
      try {
        vector = JSON.parse(vectorInput)
      } catch {
        alert("Invalid vector JSON")
        return
      }
    }

    const response = await queryMutation.mutateAsync({
      text: queryText || undefined,
      vector,
      top_k: topK,
    })
    setResults(response)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Query</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Search Text</Label>
            <Textarea
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Enter natural language query..."
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Or Raw Vector (JSON array)</Label>
            <Textarea
              value={vectorInput}
              onChange={(e) => setVectorInput(e.target.value)}
              placeholder='[0.1, 0.2, 0.3, ...]'
              rows={2}
              className="font-mono text-xs"
            />
          </div>
          <div className="flex items-center space-x-4">
            <div className="space-y-2">
              <Label>Top K</Label>
              <Input
                type="number"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                min={1}
                max={100}
                className="w-24"
              />
            </div>
            <div className="flex-1" />
            <Button onClick={handleSearch} disabled={queryMutation.isPending}>
              <Search className="h-4 w-4 mr-2" />
              {queryMutation.isPending ? "Searching..." : "Search"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <ResultsView response={results} isLoading={queryMutation.isPending} />
    </div>
  )
}
