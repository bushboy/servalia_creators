import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from 'axios';
import { getRuntimeConfig, runtimeOrVite } from '@/lib/runtimeConfig';

const API_BASE_URL =
  runtimeOrVite(
    getRuntimeConfig().apiBaseUrl,
    import.meta.env.VITE_API_BASE_URL
  ) || '';

// Tokens and API keys are held in memory only; they are never persisted to
// browser storage. The OIDC user store (managed by oidc-client-ts) uses
// sessionStorage so the user can reload during the same browser session.
let _accessToken: string | null = null;
let _apiKey: string | null = null;

export const CURRENT_TENANT_ID_KEY = 'servalia_current_tenant_id';

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

export function setApiKey(apiKey: string | null): void {
  _apiKey = apiKey;
}

export function clearAuth(): void {
  _accessToken = null;
  _apiKey = null;
  // Clear leftover keys from older builds that persisted credentials.
  localStorage.removeItem('servalia_access_token');
  localStorage.removeItem('servalia_api_key');
}

function getAuthHeader(): string | null {
  if (_accessToken) {
    return `Bearer ${_accessToken}`;
  }
  if (_apiKey) {
    return `ApiKey ${_apiKey}`;
  }
  return null;
}

function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const auth = getAuthHeader();
    if (auth) {
      config.headers.set('Authorization', auth);
    }
    const tenantId = localStorage.getItem(CURRENT_TENANT_ID_KEY);
    if (tenantId) {
      config.headers.set('X-Tenant-Id', tenantId);
    }
    config.headers.set('X-Request-ID', generateRequestId());
    if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
      config.headers.delete('Content-Type');
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (!error.response) {
      return Promise.reject(error);
    }

    const status = error.response.status;

    if (status === 401) {
      clearAuth();
      window.dispatchEvent(
        new CustomEvent('servalia:auth-error', {
          detail: { status, message: error.message },
        })
      );
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }

    if (status === 403) {
      // Keep the session. Callers surface detail via getApiErrorMessage /
      // ApiErrorAlert / mutation toasts — do not log out.
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export default api;
