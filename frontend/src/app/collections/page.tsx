"use client"

import { useState } from "react"
import { Plus, Database, AlertCircle } from "lucide-react"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { CollectionCard } from "@/components/collections/CollectionCard"
import { CollectionForm } from "@/components/collections/CollectionForm"
import { useCollections } from "@/hooks/useCollections"

export default function CollectionsPage() {
  const [showForm, setShowForm] = useState(false)
  const [search, setSearch] = useState("")
  const { data, isLoading, error } = useCollections()

  const filtered = data?.items.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.description?.toLowerCase().includes(search.toLowerCase()) ?? false),
  )

  return (
    <DashboardLayout title="Collections">
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <Input
            placeholder="Search collections..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <Button onClick={() => setShowForm(!showForm)}>
            <Plus className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Create Collection</span>
            <span className="sm:hidden">New</span>
          </Button>
        </div>

        {showForm && (
          <Card>
            <CardContent className="pt-6">
              <CollectionForm onSuccess={() => setShowForm(false)} />
            </CardContent>
          </Card>
        )}

        {error ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <AlertCircle className="h-12 w-12 text-destructive mb-4" />
              <h3 className="text-lg font-semibold mb-2">Failed to load collections</h3>
              <p className="text-sm text-muted-foreground">
                Check that the backend API is running and try again.
              </p>
            </CardContent>
          </Card>
        ) : isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="h-48 animate-pulse bg-muted" />
            ))}
          </div>
        ) : filtered && filtered.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((c) => (
              <CollectionCard key={c.id} collection={c} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Database className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {search ? "No matching collections" : "No collections yet"}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {search
                  ? "Try a different search term"
                  : "Create your first collection to start storing vectors"}
              </p>
              {!search && (
                <Button onClick={() => setShowForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Collection
                </Button>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
