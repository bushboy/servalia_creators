import { useState } from 'react';
import { NavLink as RouterNavLink } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { roleFlags } from '@/lib/navRoles';
import {
  AlertTriangle,
  BookOpen,
  Building2,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  User,
  X,
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
}

function NavItem({ to, icon, label }: NavItemProps) {
  return (
    <RouterNavLink
      to={to}
      end={to === '/dashboard'}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        )
      }
    >
      {icon}
      {label}
    </RouterNavLink>
  );
}

export function Layout({ children }: LayoutProps) {
  const { tenant, tenants, currentTenantId, authMode, switchTenant, logout } =
    useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAdmin, isOperator } = roleFlags(tenant?.roles);
  const isTenantActive = tenant?.status === 'active';
  const canSwitchTenant = authMode === 'oidc' && tenants.length > 1;

  const navItems = (
    <>
      <NavItem to="/dashboard" icon={<LayoutDashboard className="h-4 w-4" />} label="Home" />
      <NavItem
        to="/library"
        icon={<BookOpen className="h-4 w-4" />}
        label="Library"
      />
      {isOperator && (
        <NavItem
          to="/audit"
          icon={<ClipboardList className="h-4 w-4" />}
          label="Audit"
        />
      )}
      {isAdmin && (
        <NavItem
          to="/settings"
          icon={<Settings className="h-4 w-4" />}
          label="Settings"
        />
      )}
      {isAdmin && (
        <NavItem
          to="/tenants"
          icon={<Building2 className="h-4 w-4" />}
          label="Tenants"
        />
      )}
    </>
  );

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 flex-col border-r bg-card md:flex">
        <div className="flex items-center gap-2 border-b px-4 py-4 text-lg font-semibold text-foreground">
          <img src="/creator_trust.png" alt="CreatorTrust" className="h-8 w-8 object-contain" />
          CreatorTrust
        </div>

        <nav className="flex-1 space-y-1 p-3" aria-label="Main">
          {navItems}
        </nav>

        <div className="border-t p-4">
          <Button
            variant="ghost"
            className="w-full justify-start"
            size="sm"
            onClick={() => logout()}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Log out
          </Button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b bg-card px-4 md:hidden">
          <div className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <img src="/creator_trust.png" alt="CreatorTrust" className="h-7 w-7 object-contain" />
            CreatorTrust
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)}>
              <Menu className="h-5 w-5" />
            </Button>
          </div>
        </header>

        {mobileOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <div
              className="absolute inset-0 bg-black/50"
              onClick={() => setMobileOpen(false)}
            />
            <div className="absolute right-0 top-0 h-full w-64 border-l bg-card p-4 shadow-lg">
              <div className="mb-4 flex items-center justify-between">
                <span className="font-semibold">Menu</span>
                <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)}>
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <nav className="space-y-1" onClick={() => setMobileOpen(false)}>
                {navItems}
              </nav>
              <div className="mt-4 border-t pt-4">
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  size="sm"
                  onClick={() => logout()}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </Button>
              </div>
            </div>
          </div>
        )}

        <header className="hidden h-14 items-center justify-between border-b bg-card px-6 md:flex">
          <div />
          <div className="flex items-center gap-4">
            {canSwitchTenant && (
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <select
                  aria-label="Switch tenant"
                  value={currentTenantId ?? ''}
                  onChange={(e) => switchTenant(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {tenants.map((t) => (
                    <option key={t.tenant_id} value={t.tenant_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
            {tenant && (
              <div className="flex items-center gap-3 text-sm">
                <div className="text-right">
                  <div className="font-medium text-foreground">{tenant.name}</div>
                  <div className="text-muted-foreground">
                    {tenant.roles.join(', ')}
                  </div>
                </div>
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                  <User className="h-4 w-4 text-primary" />
                </div>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 p-4 md:p-6">
          {tenant && !isTenantActive && (
            <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-100">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
                <div>
                  <p className="font-medium">Tenant is {tenant.status}</p>
                  <p className="text-sm opacity-90">
                    This tenant is not active. Some actions may be unavailable
                    until an administrator re-activates it.
                  </p>
                </div>
              </div>
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
