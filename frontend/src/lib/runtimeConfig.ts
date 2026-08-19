/**
 * Runtime config for Docker / nginx deployments.
 * Build-time Vite env remains the fallback for local `npm run dev`.
 */
export type RuntimeConfig = {
  apiBaseUrl?: string;
  oidcAuthority?: string;
  oidcClientId?: string;
  oidcRedirectUri?: string;
  oidcPostLogoutRedirectUri?: string;
  oidcScope?: string;
  oidcSilentRedirectUri?: string;
};

declare global {
  interface Window {
    __RUNTIME_CONFIG__?: RuntimeConfig;
  }
}

export function getRuntimeConfig(): RuntimeConfig {
  if (typeof window === 'undefined') return {};
  return window.__RUNTIME_CONFIG__ || {};
}

export function runtimeOrVite(
  runtimeValue: string | undefined,
  viteValue: string | undefined
): string | undefined {
  const runtime = runtimeValue?.trim();
  if (runtime) return runtime;
  const vite = viteValue?.trim();
  if (vite) return vite;
  return undefined;
}
