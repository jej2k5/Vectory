"use client"

import { useState } from "react"
import { Plus, Trash2, Key, Copy, AlertCircle } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ConfirmDialog } from "@/components/ui/confirm-dialog"
import { keysApi, systemApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { showToast } from "@/hooks/useToast"

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [newKeyName, setNewKeyName] = useState("")
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null)

  const { data: keys, error: keysError } = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => keysApi.list(),
  })

  const { data: models } = useQuery({
    queryKey: ["models"],
    queryFn: () => systemApi.models(),
  })

  const { data: sysInfo } = useQuery({
    queryKey: ["system-info"],
    queryFn: () => systemApi.info(),
  })

  const createKey = useMutation({
    mutationFn: (name: string) => keysApi.create({ name }),
    onSuccess: (data) => {
      setCreatedKey(data.raw_key)
      setNewKeyName("")
      queryClient.invalidateQueries({ queryKey: ["api-keys"] })
      showToast({ title: "API key created", variant: "success" })
    },
    onError: () => {
      showToast({ title: "Failed to create API key", variant: "destructive" })
    },
  })

  const deleteKey = useMutation({
    mutationFn: (id: string) => keysApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] })
      showToast({ title: "API key revoked", variant: "success" })
    },
    onError: () => {
      showToast({ title: "Failed to revoke API key", variant: "destructive" })
    },
  })

  const handleCopyKey = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey)
      showToast({ title: "Copied to clipboard", variant: "default" })
    }
  }

  return (
    <DashboardLayout title="Settings">
      <Tabs defaultValue="api-keys">
        <TabsList>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create API Key</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  if (newKeyName) createKey.mutate(newKeyName)
                }}
                className="flex items-end gap-4"
              >
                <div className="flex-1 space-y-2">
                  <Label>Key Name</Label>
                  <Input
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="My API Key"
                    required
                  />
                </div>
                <Button type="submit" disabled={!newKeyName || createKey.isPending}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create
                </Button>
              </form>
              {createdKey && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                  <p className="text-sm font-medium text-green-800">
                    API Key created! Copy it now - it won&apos;t be shown again:
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <code className="text-xs flex-1 font-mono break-all bg-white p-2 rounded border">
                      {createdKey}
                    </code>
                    <Button variant="outline" size="sm" onClick={handleCopyKey}>
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {keysError ? (
            <Card>
              <CardContent className="flex items-center gap-3 py-6">
                <AlertCircle className="h-5 w-5 text-destructive" />
                <p className="text-sm text-muted-foreground">
                  Failed to load API keys. Check that the backend is running.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {keys?.map((key) => (
                <Card key={key.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div className="flex items-center space-x-3">
                      <Key className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{key.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Created {formatDate(key.created_at)}
                          {key.last_used_at && ` | Last used ${formatDate(key.last_used_at)}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      <Badge variant={key.is_active ? "success" : "secondary"}>
                        {key.is_active ? "Active" : "Revoked"}
                      </Badge>
                      {key.is_active && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteKeyId(key.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
              {keys && keys.length === 0 && (
                <Card>
                  <CardContent className="flex flex-col items-center py-8">
                    <Key className="h-8 w-8 text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">No API keys yet</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="models" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Available Embedding Models</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {models?.map((model) => (
                  <div
                    key={model.name}
                    className="flex items-center justify-between p-3 border rounded"
                  >
                    <div>
                      <p className="font-medium">{model.name}</p>
                      <p className="text-xs text-muted-foreground">{model.provider}</p>
                    </div>
                    <Badge variant="outline">{model.dimensions}d</Badge>
                  </div>
                ))}
                {models && models.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No models available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
            </CardHeader>
            <CardContent>
              {sysInfo ? (
                <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                  {JSON.stringify(sysInfo, null, 2)}
                </pre>
              ) : (
                <p className="text-sm text-muted-foreground">Loading system information...</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ConfirmDialog
        open={!!deleteKeyId}
        onOpenChange={(open) => {
          if (!open) setDeleteKeyId(null)
        }}
        title="Revoke API key"
        description="Are you sure you want to revoke this API key? Any applications using this key will lose access immediately."
        confirmLabel="Revoke"
        variant="destructive"
        onConfirm={() => {
          if (deleteKeyId) {
            deleteKey.mutate(deleteKeyId)
            setDeleteKeyId(null)
          }
        }}
        loading={deleteKey.isPending}
      />
    </DashboardLayout>
  )
}
