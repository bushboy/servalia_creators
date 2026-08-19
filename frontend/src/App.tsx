import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { AdminRoute } from '@/components/auth/AdminRoute';
import { OperatorRoute } from '@/components/auth/OperatorRoute';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Toaster } from '@/components/ui/sonner';
import { AuditPage } from '@/pages/Audit';
import { AuthorSetupPage } from '@/pages/AuthorSetup';
import { AssetsPage } from '@/pages/Assets';
import { BookAuthorSetupPage } from '@/pages/BookAuthorSetup';
import { BookWorkspacePage } from '@/pages/BookWorkspace';
import { CreateTenantPage } from '@/pages/CreateTenant';
import { Dashboard } from '@/pages/Dashboard';
import { GovernancePage } from '@/pages/Governance';
import { LaunchPage } from '@/pages/Launch';
import { LibraryPage } from '@/pages/Library';
import { LoginCallbackPage } from '@/pages/LoginCallback';
import { LoginPage } from '@/pages/Login';
import { LogoutPage } from '@/pages/Logout';
import { ManuscriptPage } from '@/pages/Manuscript';
import { PublishingPage } from '@/pages/Publishing';
import { ApiKeysSettings } from '@/pages/settings/ApiKeys';
import { MembersSettings } from '@/pages/settings/Members';
import { SettingsLayout } from '@/pages/settings/SettingsLayout';
import { SystemSettings } from '@/pages/settings/System';
import { TenantSettings } from '@/pages/settings/Tenant';
import { TenantsPage } from '@/pages/Tenants';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/login/callback" element={<LoginCallbackPage />} />
      <Route path="/logout" element={<LogoutPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/author"
        element={
          <ProtectedRoute>
            <AuthorSetupPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/library"
        element={
          <ProtectedRoute>
            <LibraryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId"
        element={
          <ProtectedRoute>
            <BookWorkspacePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId/setup"
        element={
          <ProtectedRoute>
            <BookAuthorSetupPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId/manuscript"
        element={
          <ProtectedRoute>
            <ManuscriptPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId/assets"
        element={
          <ProtectedRoute>
            <AssetsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId/governance"
        element={
          <ProtectedRoute>
            <GovernancePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId/publishing"
        element={
          <ProtectedRoute>
            <PublishingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/books/:bookId/launch"
        element={
          <ProtectedRoute>
            <LaunchPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit"
        element={
          <OperatorRoute>
            <AuditPage />
          </OperatorRoute>
        }
      />
      <Route
        path="/tenants"
        element={
          <AdminRoute>
            <TenantsPage />
          </AdminRoute>
        }
      />
      <Route
        path="/create-tenant"
        element={
          <ProtectedRoute>
            <CreateTenantPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <AdminRoute>
            <SettingsLayout />
          </AdminRoute>
        }
      >
        <Route index element={<Navigate to="/settings/tenant" replace />} />
        <Route path="tenant" element={<TenantSettings />} />
        <Route path="api-keys" element={<ApiKeysSettings />} />
        <Route path="members" element={<MembersSettings />} />
        <Route path="system" element={<SystemSettings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <ErrorBoundary>
        <AppRoutes />
        <Toaster position="top-right" richColors closeButton />
      </ErrorBoundary>
    </AuthProvider>
  );
}

export default App;
