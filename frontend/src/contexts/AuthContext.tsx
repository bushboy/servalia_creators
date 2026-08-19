import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import api, {
  CURRENT_TENANT_ID_KEY,
  setAccessToken,
  setApiKey,
} from '@/lib/api';
import {
  clearAuth,
  getUser,
  isOidcConfigured,
  signinRedirect,
  signinRedirectCallback,
  signoutRedirect,
} from '@/lib/auth';
import { fetchMyTenants } from '@/lib/api/queries';
import { Tenant, TenantInfo } from '@/types';

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: Error | null;
  tenant: TenantInfo | null;
  tenants: Tenant[];
  currentTenantId: string | null;
  authMode: 'oidc' | 'apikey';
  loginWithRedirect: () => Promise<void>;
  loginWithApiKey: (apiKey: string) => Promise<void>;
  handleCallback: () => Promise<void>;
  switchTenant: (tenantId: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(true);
  const [hasCredentials, setHasCredentials] = useState(false);
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [currentTenantId, setCurrentTenantId] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const queryClient = useQueryClient();

  const authMode: 'oidc' | 'apikey' = isOidcConfigured ? 'oidc' : 'apikey';

  const loadTenant = useCallback(async () => {
    try {
      const { data } = await api.get<TenantInfo>('/me');
      setTenant(data);
      setError(null);
    } catch (err) {
      setTenant(null);
      setError(err instanceof Error ? err : new Error(String(err)));
      throw err;
    }
  }, []);

  const selectTenantAndLoad = useCallback(
    async (tenantId: string) => {
      localStorage.setItem(CURRENT_TENANT_ID_KEY, tenantId);
      setCurrentTenantId(tenantId);
      await loadTenant();
    },
    [loadTenant]
  );

  const loadTenants = useCallback(async () => {
    if (authMode !== 'oidc') {
      return [];
    }
    try {
      const list = await fetchMyTenants();
      setTenants(list);

      const storedId = localStorage.getItem(CURRENT_TENANT_ID_KEY);
      const active =
        list.find((t) => t.tenant_id === storedId) ||
        list.find((t) => t.status === 'active') ||
        list[0];

      if (active) {
        await selectTenantAndLoad(active.tenant_id);
      } else {
        localStorage.removeItem(CURRENT_TENANT_ID_KEY);
        setCurrentTenantId(null);
        setTenant(null);
      }
      return list;
    } catch (err) {
      setTenants([]);
      setTenant(null);
      throw err;
    }
  }, [authMode, selectTenantAndLoad]);

  useEffect(() => {
    let mounted = true;

    async function init() {
      try {
        if (authMode === 'oidc') {
          const user = await getUser();
          if (user && !user.expired && user.access_token) {
            setHasCredentials(true);
            setAccessToken(user.access_token);
            const list = await loadTenants();
            if (list.length === 0 && location.pathname !== '/create-tenant') {
              navigate('/create-tenant', { replace: true });
            }
          }
        }
        // API keys are not persisted; the user must re-authenticate on reload.
      } catch {
        clearAuth();
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    init();
    return () => {
      mounted = false;
    };
  }, [authMode, loadTenant, loadTenants, location.pathname, navigate]);

  useEffect(() => {
    const handler = () => {
      setHasCredentials(false);
      clearAuth();
      setTenant(null);
      setTenants([]);
      setCurrentTenantId(null);
      navigate('/login', { replace: true });
    };
    window.addEventListener('servalia:auth-error', handler);
    return () => window.removeEventListener('servalia:auth-error', handler);
  }, [navigate]);

  const loginWithRedirect = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      await signinRedirect();
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      setIsLoading(false);
    }
  }, []);

  const loginWithApiKey = useCallback(
    async (apiKey: string) => {
      setError(null);
      setIsLoading(true);
      try {
        setApiKey(apiKey);
        setHasCredentials(true);
        await loadTenant();
        const from = (location.state as { from?: string })?.from || '/';
        navigate(from, { replace: true });
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
        setHasCredentials(false);
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    },
    [loadTenant, location.state, navigate]
  );

  const handleCallback = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      const user = await signinRedirectCallback();
      if (user?.access_token) {
        setHasCredentials(true);
        setAccessToken(user.access_token);
      }
      await loadTenants();
      const tenantList = (await api.get<{ data: Tenant[] }>('/me/tenants')).data
        .data;
      if (!tenantList || tenantList.length === 0) {
        navigate('/create-tenant', { replace: true });
      } else {
        navigate('/', { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsLoading(false);
    }
  }, [loadTenants, navigate]);

  const switchTenant = useCallback(
    async (tenantId: string) => {
      setError(null);
      setIsLoading(true);
      try {
        await selectTenantAndLoad(tenantId);
        // Wipe the React Query cache so tenant-scoped data is not shared
        // between workspaces after switching.
        queryClient.clear();
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
      } finally {
        setIsLoading(false);
      }
    },
    [selectTenantAndLoad, queryClient]
  );

  const logout = useCallback(async () => {
    clearAuth();
    setHasCredentials(false);
    localStorage.removeItem(CURRENT_TENANT_ID_KEY);
    queryClient.clear();
    setTenant(null);
    setTenants([]);
    setCurrentTenantId(null);
    setError(null);
    if (authMode === 'oidc') {
      await signoutRedirect();
    } else {
      navigate('/login', { replace: true });
    }
  }, [authMode, navigate, queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: hasCredentials,
      isLoading,
      error,
      tenant,
      tenants,
      currentTenantId,
      authMode,
      loginWithRedirect,
      loginWithApiKey,
      handleCallback,
      switchTenant,
      logout,
    }),
    [
      hasCredentials,
      tenant,
      tenants,
      currentTenantId,
      isLoading,
      error,
      authMode,
      loginWithRedirect,
      loginWithApiKey,
      handleCallback,
      switchTenant,
      logout,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
