import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';

interface OperatorRouteProps {
  children: React.ReactNode;
}

/**
 * Requires an authenticated operator or admin.
 * Viewers who deep-link see a forbidden state (session kept), not logout.
 */
export function OperatorRoute({ children }: OperatorRouteProps) {
  return (
    <ProtectedRoute>
      <OperatorGate>{children}</OperatorGate>
    </ProtectedRoute>
  );
}

function OperatorGate({ children }: { children: React.ReactNode }) {
  const { tenant, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const allowed =
    tenant?.roles.includes('operator') || tenant?.roles.includes('admin');

  if (!allowed) {
    return (
      <div className="mx-auto max-w-lg space-y-4 py-12">
        <ApiErrorAlert
          title="Forbidden"
          error={
            new Error(
              'You need an operator or admin role to use this page. Your session is still active.'
            )
          }
        />
        <Link
          to="/login"
          className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium hover:bg-accent"
        >
          Back to login
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
