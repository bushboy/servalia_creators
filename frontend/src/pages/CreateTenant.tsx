import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useCreateTenantMutation } from '@/hooks/useQueries';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

export function CreateTenantPage() {
  const navigate = useNavigate();
  const { switchTenant } = useAuth();
  const create = useCreateTenantMutation();
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [slugTouched, setSlugTouched] = useState(false);

  const derivedSlug = slug || name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !derivedSlug) return;

    try {
      const tenant = await create.mutateAsync({
        name,
        slug: derivedSlug,
      });
      await switchTenant(tenant.tenant_id);
      navigate('/', { replace: true });
    } catch {
      // Error is already toasted by the mutation hook.
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create tenant</CardTitle>
          <CardDescription>
            Set up a new tenant for your organization.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="tenant-name" className="text-sm font-medium">
                Tenant name
              </label>
              <Input
                id="tenant-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Northwind Press"
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="tenant-slug" className="text-sm font-medium">
                Slug
              </label>
              <Input
                id="tenant-slug"
                value={slugTouched ? slug : derivedSlug}
                onChange={(e) => {
                  setSlugTouched(true);
                  setSlug(e.target.value);
                }}
                placeholder="northwind-press"
              />
              <p className="text-xs text-muted-foreground">
                Lowercase letters, numbers and hyphens only. Used in URLs and
                API calls.
              </p>
            </div>

            {create.error && (
              <p className="text-sm text-destructive">{create.error.message}</p>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={create.isPending || !name || !derivedSlug}
            >
              {create.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Create tenant
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
