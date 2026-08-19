import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useMyTenants } from '@/hooks/useQueries';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { Building2, Settings, Users } from 'lucide-react';

/**
 * List tenants the user can switch into.
 * Creating a tenant is first-run only via `/create-tenant` (zero tenants).
 */
export function TenantsPage() {
  const navigate = useNavigate();
  const { switchTenant } = useAuth();
  const { data: tenants, isLoading, error } = useMyTenants();

  async function goToTenant(tenantId: string, path: string) {
    await switchTenant(tenantId);
    navigate(path);
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (error) {
    return <ApiErrorAlert title="Failed to load tenants" error={error} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Manage tenants</h1>
        <p className="text-muted-foreground">
          View tenants you have access to. Switching a tenant loads its
          customers, settings and workspace.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your tenants</CardTitle>
        </CardHeader>
        <CardContent>
          {!tenants || tenants.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              You do not have access to any tenants yet. If this is your first
              login, use the create-tenant flow.
            </p>
          ) : (
            <div className="space-y-3">
              {tenants.map((t) => (
                <div
                  key={t.tenant_id}
                  className="flex flex-col gap-3 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{t.name}</span>
                      <Badge variant="outline">{t.status}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {t.slug} • {new Date(t.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => goToTenant(t.tenant_id, '/settings/members')}
                    >
                      <Users className="mr-2 h-4 w-4" />
                      Members
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => goToTenant(t.tenant_id, '/')}
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Switch
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
