#!/bin/sh
set -eu

# Inject OIDC / API settings at container start so one image works across envs.
cat > /usr/share/nginx/html/runtime-config.js <<EOF
window.__RUNTIME_CONFIG__ = {
  apiBaseUrl: "${API_BASE_URL:-/api}",
  oidcAuthority: "${OIDC_AUTHORITY:-}",
  oidcClientId: "${OIDC_CLIENT_ID:-}",
  oidcRedirectUri: "${OIDC_REDIRECT_URI:-}",
  oidcPostLogoutRedirectUri: "${OIDC_POST_LOGOUT_REDIRECT_URI:-}",
  oidcScope: "${OIDC_SCOPE:-openid profile email}",
  oidcSilentRedirectUri: "${OIDC_SILENT_REDIRECT_URI:-}"
};
EOF

exec nginx -g "daemon off;"
