"use client"

import { useState } from "react"
import { Plus, Trash2, Key } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { DashboardLayout } from "@/components/dashboard/DashboardLayout"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { keysApi, systemApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [newKeyName, setNewKeyName] = useState("")
  const [createdKey, setCreatedKey] = useState<string | null>(null)

  const { data: keys } = useQuery({
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
    },
  })

  const deleteKey = useMutation({
    mutationFn: (id: string) => keysApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] })
    },
  })

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
              <div className="flex items-end space-x-4">
                <div className="flex-1 space-y-2">
                  <Label>Key Name</Label>
                  <Input
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="My API Key"
                  />
                </div>
                <Button
                  onClick={() => createKey.mutate(newKeyName)}
                  disabled={!newKeyName || createKey.isPending}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create
                </Button>
              </div>
              {createdKey && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
                  <p className="text-sm font-medium text-green-800">
                    API Key created! Copy it now - it won&apos;t be shown again:
                  </p>
                  <code className="text-xs mt-1 block font-mono break-all">{createdKey}</code>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-3">
            {keys?.map((key) => (
              <Card key={key.id}>
                <CardContent className="flex items-center justify-between py-4">
                  <div className="flex items-center space-x-3">
                    <Key className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{key.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Created {formatDate(key.created_at)}
                        {key.last_used_at && ` | Last used ${formatDate(key.last_used_at)}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={key.is_active ? "success" : "secondary"}>
                      {key.is_active ? "Active" : "Revoked"}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteKey.mutate(key.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
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
              {sysInfo && (
                <pre className="text-xs bg-muted p-4 rounded overflow-auto">
                  {JSON.stringify(sysInfo, null, 2)}
                </pre>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  )
}
