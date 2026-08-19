import { useState } from 'react';
import {
  useApiKeys,
  useCreateApiKeyMutation,
  useRevokeApiKeyMutation,
} from '@/hooks/useQueries';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, Trash2 } from 'lucide-react';

const ROLES = ['viewer', 'operator', 'admin'];

export function ApiKeysSettings() {
  const { data: apiKeys, isLoading, error } = useApiKeys();
  const create = useCreateApiKeyMutation();
  const revoke = useRevokeApiKeyMutation();

  const [keyId, setKeyId] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>(['viewer']);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex h-32 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 p-4 text-destructive">
        Failed to load API keys: {error.message}
      </div>
    );
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!keyId) return;
    const result = await create.mutateAsync({
      api_key_id: keyId,
      roles: selectedRoles,
    });
    setCreatedSecret(result.secret);
    setKeyId('');
  }

  async function handleRevoke(apiKeyId: string) {
    if (!confirm('Revoke this API key?')) return;
    await revoke.mutateAsync(apiKeyId);
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create API key</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="keyId" className="text-sm font-medium">
                  Key ID
                </label>
                <Input
                  id="keyId"
                  value={keyId}
                  onChange={(e) => setKeyId(e.target.value)}
                  placeholder="e.g. reporting-service"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Roles</label>
                <div className="flex gap-2">
                  {ROLES.map((role) => (
                    <label key={role} className="flex items-center gap-1 text-sm">
                      <input
                        type="checkbox"
                        checked={selectedRoles.includes(role)}
                        onChange={(e) => {
                          setSelectedRoles((prev) =>
                            e.target.checked
                              ? [...prev, role]
                              : prev.filter((r) => r !== role)
                          );
                        }}
                        className="h-4 w-4 rounded border-input text-primary focus:ring-ring"
                      />
                      {role}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {createdSecret && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-100">
                <p className="font-medium">Key created. Copy the secret now:</p>
                <code className="mt-1 block break-all font-mono">{createdSecret}</code>
              </div>
            )}

            {create.error && (
              <p className="text-sm text-destructive">{create.error.message}</p>
            )}

            <Button type="submit" disabled={create.isPending || !keyId}>
              {create.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Create key
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API keys</CardTitle>
        </CardHeader>
        <CardContent>
          {!apiKeys || apiKeys.length === 0 ? (
            <p className="text-sm text-muted-foreground">No API keys yet.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-sm">
                <thead className="bg-muted text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium">Key ID</th>
                    <th className="px-4 py-2 text-left font-medium">Roles</th>
                    <th className="px-4 py-2 text-left font-medium">Created</th>
                    <th className="px-4 py-2 text-left font-medium">Status</th>
                    <th className="px-4 py-2 text-left font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {apiKeys.map((key) => (
                    <tr key={key.api_key_id}>
                      <td className="px-4 py-3 font-mono text-xs">
                        {key.api_key_id}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {key.roles.map((role) => (
                            <Badge key={role} variant="secondary">
                              {role}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                        {new Date(key.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        {key.revoked ? (
                          <Badge variant="outline">Revoked</Badge>
                        ) : (
                          <Badge>Active</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRevoke(key.api_key_id)}
                          disabled={revoke.isPending || key.revoked}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
