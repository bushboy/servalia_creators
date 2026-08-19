import { NavLink as RouterNavLink, Outlet } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface TabProps {
  to: string;
  label: string;
}

function Tab({ to, label }: TabProps) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'inline-flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
          isActive
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        )
      }
    >
      {label}
    </RouterNavLink>
  );
}

export function SettingsLayout() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage tenant details, API keys, members, and system health.
        </p>
      </div>

      <nav className="flex gap-2 border-b pb-2">
        <Tab to="/settings/tenant" label="Tenant" />
        <Tab to="/settings/api-keys" label="API keys" />
        <Tab to="/settings/members" label="Members" />
        <Tab to="/settings/system" label="System" />
      </nav>

      <Outlet />
    </div>
  );
}
