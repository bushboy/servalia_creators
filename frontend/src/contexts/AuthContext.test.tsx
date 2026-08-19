import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('@/lib/auth', () => ({
  isOidcConfigured: false,
  getUser: vi.fn().mockResolvedValue(null),
  clearAuth: vi.fn(),
  signinRedirect: vi.fn(),
  signinRedirectCallback: vi.fn(),
  signoutRedirect: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  setAccessToken: vi.fn(),
  setApiKey: vi.fn(),
  clearAuth: vi.fn(),
  CURRENT_TENANT_ID_KEY: 'servalia_current_tenant_id',
  default: { get: vi.fn(), post: vi.fn() },
}));

vi.mock('@/lib/api/queries', () => ({
  fetchMyTenants: vi.fn().mockResolvedValue([]),
}));

import { AuthProvider, useAuth } from '@/contexts/AuthContext';

function Probe() {
  const { authMode, isAuthenticated, isLoading } = useAuth();
  return (
    <div>
      <span data-testid="mode">{authMode}</span>
      <span data-testid="auth">{String(isAuthenticated)}</span>
      <span data-testid="loading">{String(isLoading)}</span>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('defaults to API-key mode when OIDC is not configured', async () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <AuthProvider>
            <Probe />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });
    expect(screen.getByTestId('mode').textContent).toBe('apikey');
    expect(screen.getByTestId('auth').textContent).toBe('false');
  });
});
