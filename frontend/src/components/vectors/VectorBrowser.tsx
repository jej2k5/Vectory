"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { VectorTable } from "@/components/vectors/VectorTable"
import { useCollectionVectors } from "@/hooks/useVectors"

interface VectorBrowserProps {
  collectionId: string
}

export function VectorBrowser({ collectionId }: VectorBrowserProps) {
  const [page, setPage] = useState(1)
  const pageSize = 10
  const skip = (page - 1) * pageSize

  const { data, isLoading } = useCollectionVectors(collectionId, skip, pageSize)

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-muted-foreground">
          Loading vectors...
        </CardContent>
      </Card>
    )
  }

  if (!data || data.total === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-muted-foreground">
          No vectors in this collection yet. Ingest a document or insert vectors to get started.
        </CardContent>
      </Card>
    )
  }

  return (
    <VectorTable
      vectors={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      collectionId={collectionId}
    />
  )
}
