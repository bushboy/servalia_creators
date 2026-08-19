import { useAuth } from '@/contexts/AuthContext';

interface RoleGateProps {
  roles: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RoleGate({ roles, children, fallback = null }: RoleGateProps) {
  const { tenant } = useAuth();
  const hasRole = tenant?.roles.some((role) => roles.includes(role)) ?? false;

  if (!hasRole) {
    return fallback;
  }

  return children;
}
