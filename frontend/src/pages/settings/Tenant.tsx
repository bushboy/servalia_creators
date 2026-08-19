import { useState } from 'react';
import {
  useTenantDetails,
  useUpdateTenantMutation,
} from '@/hooks/useQueries';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

export function TenantSettings() {
  const { data: tenant, isLoading, error } = useTenantDetails();
  const update = useUpdateTenantMutation();

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [saved, setSaved] = useState(false);

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
        Failed to load tenant details: {error.message}
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        No tenant details available.
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: { name?: string; slug?: string } = {};
    if (name) payload.name = name;
    if (slug) payload.slug = slug;
    if (!payload.name && !payload.slug) return;

    await update.mutateAsync(payload);
    setSaved(true);
    setName('');
    setSlug('');
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Tenant details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-6 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Name</p>
            <p>{tenant.name}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Slug</p>
            <p>{tenant.slug}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Status</p>
            <p>{tenant.status}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">Created</p>
            <p>{new Date(tenant.created_at).toLocaleString()}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Update name
              </label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={tenant.name}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="slug" className="text-sm font-medium">
                Update slug
              </label>
              <Input
                id="slug"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder={tenant.slug}
              />
            </div>
          </div>

          {saved && (
            <p className="text-sm text-emerald-600">Tenant updated successfully.</p>
          )}
          {update.error && (
            <p className="text-sm text-destructive">{update.error.message}</p>
          )}

          <Button type="submit" disabled={update.isPending || (!name && !slug)}>
            {update.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            Save changes
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
