"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { VectorTable } from "@/components/vectors/VectorTable"
import { VectorVisualization } from "@/components/vectors/VectorVisualization"
import { formatDuration } from "@/lib/utils"
import type { QueryResponse, VectorResult } from "@/types"

interface ResultsViewProps {
  response: QueryResponse | null
  isLoading: boolean
}

export function ResultsView({ response, isLoading }: ResultsViewProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-muted-foreground">Searching...</CardContent>
      </Card>
    )
  }

  if (!response) return null

  const vectorResults: VectorResult[] = response.results.map((r: any) => ({
    id: r.id,
    collection_id: "",
    metadata: r.metadata || {},
    text_content: r.text_content,
    source_file: null,
    chunk_index: null,
    created_at: new Date().toISOString(),
    score: r.score,
  }))

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <Badge variant="secondary">{response.total} results</Badge>
        <Badge variant="outline">{formatDuration(response.latency_ms)}</Badge>
      </div>

      <Tabs defaultValue="table">
        <TabsList>
          <TabsTrigger value="table">Table</TabsTrigger>
          <TabsTrigger value="visualization">Visualization</TabsTrigger>
        </TabsList>
        <TabsContent value="table">
          <VectorTable
            vectors={vectorResults}
            total={response.total}
            page={1}
            onPageChange={() => {}}
          />
        </TabsContent>
        <TabsContent value="visualization">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Score Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <VectorVisualization results={vectorResults} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
