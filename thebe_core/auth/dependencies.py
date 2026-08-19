from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request

from thebe_core.auth.exceptions import AuthenticationError, AuthorizationError
from thebe_core.auth.models import TenantContext
from thebe_core.auth.service import AuthService


def _parse_authorization(header: str | None) -> tuple[str, str] | None:
    if not header:
        return None
    parts = header.split(" ", 1)
    if len(parts) != 2:
        return None
    return parts[0].lower(), parts[1]


async def get_current_subject(
    authorization: str | None = Header(default=None),
    request: Request = None,  # type: ignore[assignment]
) -> str:
    """Return the authenticated OIDC subject for tenant creation flows.

    Only Bearer tokens are accepted; API keys cannot create tenants.
    """
    auth_service: AuthService = request.app.state.auth_service
    parsed = _parse_authorization(authorization)
    if not parsed:
        raise HTTPException(status_code=401, detail="Missing credentials")

    scheme, credential = parsed
    if scheme != "bearer":
        raise HTTPException(
            status_code=401, detail="Tenant creation requires a Bearer token"
        )

    try:
        return await auth_service.validate_bearer_token(credential)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def get_tenant_context(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None),
    request: Request = None,  # type: ignore[assignment]
) -> TenantContext:
    """Extract and validate the caller's tenant context.

    Accepts:
      - `Authorization: Bearer <oidc-jwt>`
      - `Authorization: ApiKey <api-key-id>:<secret>`
      - `X-API-Key: <api-key-id>:<secret>` (convenience for M2M calls)
    """
    auth_service = request.app.state.auth_service

    parsed = _parse_authorization(authorization)
    if parsed:
        scheme, credential = parsed
    elif x_api_key:
        scheme, credential = "apikey", x_api_key
    else:
        raise HTTPException(status_code=401, detail="Missing credentials")

    if scheme not in {"bearer", "apikey"}:
        raise HTTPException(status_code=401, detail="Unsupported authorization scheme")

    try:
        return await auth_service.get_tenant_context(
            scheme, credential, tenant_hint=x_tenant_id
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except AuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


class RoleRequired:
    """Dependency factory that enforces one or more roles."""

    def __init__(self, roles: list[str]) -> None:
        self.roles = set(roles)

    async def __call__(
        self, tenant_context: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        if not any(tenant_context.has_role(r) for r in self.roles):
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {sorted(self.roles)}",
            )
        return tenant_context
