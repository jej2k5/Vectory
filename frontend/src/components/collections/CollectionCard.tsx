"use client"

import Link from "next/link"
import { Database } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatBytes, formatRelativeDate, truncate } from "@/lib/utils"
import type { Collection } from "@/types"

interface CollectionCardProps {
  collection: Collection
}

export function CollectionCard({ collection }: CollectionCardProps) {
  return (
    <Link href={`/collections/${collection.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span>{collection.name}</span>
            </CardTitle>
            <Badge variant="secondary">{collection.distance_metric}</Badge>
          </div>
          {collection.description && (
            <p className="text-sm text-muted-foreground">
              {truncate(collection.description, 100)}
            </p>
          )}
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Vectors</p>
              <p className="font-medium">{collection.vector_count.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Dimension</p>
              <p className="font-medium">{collection.dimension}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Model</p>
              <p className="font-medium text-xs">{truncate(collection.embedding_model, 20)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Created</p>
              <p className="font-medium text-xs">{formatRelativeDate(collection.created_at)}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
