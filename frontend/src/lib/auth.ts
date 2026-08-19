import { User, UserManager, WebStorageStateStore } from 'oidc-client-ts';
import { clearAuth as clearApiAuth } from './api';
import { getRuntimeConfig, runtimeOrVite } from './runtimeConfig';

const runtime = getRuntimeConfig();

const authority = runtimeOrVite(
  runtime.oidcAuthority,
  import.meta.env.VITE_OIDC_AUTHORITY
);
const clientId = runtimeOrVite(
  runtime.oidcClientId,
  import.meta.env.VITE_OIDC_CLIENT_ID
);
const redirectUri = runtimeOrVite(
  runtime.oidcRedirectUri,
  import.meta.env.VITE_OIDC_REDIRECT_URI
);
const scope =
  runtimeOrVite(runtime.oidcScope, import.meta.env.VITE_OIDC_SCOPE) ||
  'openid profile email';
const silentRedirectUri = runtimeOrVite(
  runtime.oidcSilentRedirectUri,
  import.meta.env.VITE_OIDC_SILENT_REDIRECT_URI
);
const postLogoutRedirectUri =
  runtimeOrVite(
    runtime.oidcPostLogoutRedirectUri,
    import.meta.env.VITE_OIDC_POST_LOGOUT_REDIRECT_URI
  ) || `${window.location.origin}/login`;

export const isOidcConfigured = Boolean(authority && clientId && redirectUri);

export const userManager = isOidcConfigured
  ? new UserManager({
      authority: authority!,
      client_id: clientId!,
      redirect_uri: redirectUri!,
      response_type: 'code',
      scope,
      automaticSilentRenew: true,
      accessTokenExpiringNotificationTimeInSeconds: 60,
      silent_redirect_uri: silentRedirectUri || redirectUri!,
      // User and state are kept in sessionStorage, never localStorage, so
      // OIDC tokens do not survive a full browser restart.
      userStore: new WebStorageStateStore({ store: window.sessionStorage }),
      stateStore: new WebStorageStateStore({ store: window.sessionStorage }),
    })
  : null;

export async function signinRedirect(): Promise<void> {
  if (!userManager) {
    throw new Error('OIDC is not configured');
  }
  return userManager.signinRedirect();
}

export async function signinRedirectCallback(): Promise<User> {
  if (!userManager) {
    throw new Error('OIDC is not configured');
  }
  return userManager.signinRedirectCallback();
}

export async function signoutRedirect(): Promise<void> {
  if (!userManager) {
    return;
  }
  return userManager.signoutRedirect({
    post_logout_redirect_uri: postLogoutRedirectUri,
  });
}

export async function getUser(): Promise<User | null> {
  if (!userManager) {
    return null;
  }
  return userManager.getUser();
}

export function clearAuth(): void {
  clearApiAuth();
  localStorage.removeItem('servalia_auth_mode');
  if (userManager) {
    userManager.removeUser().catch(() => {});
  }
}
