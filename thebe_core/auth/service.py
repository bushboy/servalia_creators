from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from thebe_core.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)
from thebe_core.auth.models import (
    APIKeyDB,
    TenantContext,
    TenantDB,
    TenantMembershipDB,
    hash_api_key_secret,
)
from thebe_core.auth.provider import IdentityProvider, OIDCIdentityProvider
from thebe_core.config import settings


def _is_super_admin(subject: str) -> bool:
    """Check whether an external OIDC subject has super-admin privileges."""
    if not settings.SUPER_ADMIN_SUBJECTS:
        return False
    allowed = {
        s.strip() for s in settings.SUPER_ADMIN_SUBJECTS.split(",") if s.strip()
    }
    return subject in allowed


class AuthService:
    """Async service for tenants, memberships, API keys and token validation."""

    def __init__(self, engine, provider: IdentityProvider | None = None) -> None:
        self.engine = engine
        self._provider = provider

        if provider is None and settings.OIDC_ISSUER_URL:
            self._provider = OIDCIdentityProvider()

    # ------------------------------------------------------------------
    # Context extraction
    # ------------------------------------------------------------------

    async def get_tenant_context(
        self,
        scheme: str,
        credential: str,
        tenant_hint: str | None = None,
    ) -> TenantContext:
        """Authenticate a request and return the resolved tenant context."""
        if scheme.lower() == "bearer":
            return await self._context_from_bearer(credential, tenant_hint)
        if scheme.lower() == "apikey":
            return await self._context_from_api_key(credential)
        raise AuthenticationError(f"Unsupported authorization scheme: {scheme}")

    async def validate_bearer_token(self, token: str) -> str:
        """Validate a bearer token and return the external subject id."""
        if self._provider is None:
            raise AuthenticationError("OIDC is not configured")
        try:
            return self._provider.validate_token(token)
        except Exception as exc:
            raise AuthenticationError(f"Invalid bearer token: {exc}") from exc

    async def _context_from_bearer(
        self, token: str, tenant_hint: str | None
    ) -> TenantContext:
        if self._provider is None:
            raise AuthenticationError("OIDC is not configured")

        try:
            subject = self._provider.validate_token(token)
        except Exception as exc:
            raise AuthenticationError(f"Invalid bearer token: {exc}") from exc

        async with AsyncSession(self.engine) as session:
            stmt = select(TenantMembershipDB).where(
                TenantMembershipDB.subject == subject,
                TenantMembershipDB.revoked.is_(False),
            )
            result = await session.execute(stmt)
            rows = list(result.scalars().all())

            if not rows:
                if _is_super_admin(subject):
                    if not tenant_hint:
                        raise AuthorizationError(
                            "Super admin must provide X-Tenant-Id"
                        )
                    tenant = await self.get_tenant(tenant_hint)
                    if tenant is None:
                        raise AuthorizationError("Invalid tenant")
                    return TenantContext(
                        tenant_id=tenant.tenant_id,
                        subject=subject,
                        roles=["admin"],
                        auth_method="bearer",
                    )
                raise AuthorizationError("No active tenant membership for subject")

            if len(rows) == 1:
                membership = rows[0]
            elif tenant_hint:
                matches = [r for r in rows if r.tenant_id == tenant_hint]
                if not matches:
                    raise AuthorizationError(
                        "Subject is not a member of the requested tenant"
                    )
                membership = matches[0]
            else:
                raise AuthorizationError(
                    "Subject belongs to multiple tenants; provide X-Tenant-Id"
                )

            return TenantContext(
                tenant_id=membership.tenant_id,
                subject=subject,
                roles=[membership.role],
                auth_method="bearer",
            )

    async def _context_from_api_key(self, credentials: str) -> TenantContext:
        if ":" not in credentials:
            raise AuthenticationError(
                "API key must be formatted as '<api_key_id>:<secret>'"
            )

        api_key_id, secret = credentials.split(":", 1)

        async with AsyncSession(self.engine) as session:
            row = await session.get(APIKeyDB, api_key_id)
            if row is None:
                raise AuthenticationError("Unknown API key")

            if not row.verify_secret(secret):
                raise AuthenticationError("Invalid API key secret")

            if row.revoked:
                raise AuthenticationError("API key has been revoked")

            if row.expires_at and row.expires_at < datetime.now(timezone.utc):
                raise AuthenticationError("API key has expired")

            return TenantContext(
                tenant_id=row.tenant_id,
                api_key_id=api_key_id,
                roles=list(row.roles),
                auth_method="api_key",
            )

    # ------------------------------------------------------------------
    # Provisioning helpers
    # ------------------------------------------------------------------

    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        slug: str,
    ) -> TenantDB:
        tenant = TenantDB(tenant_id=tenant_id, name=name, slug=slug)
        async with AsyncSession(self.engine) as session:
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> TenantDB | None:
        async with AsyncSession(self.engine) as session:
            stmt = select(TenantDB).where(TenantDB.slug == slug)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_tenants_for_subject(
        self, subject: str
    ) -> list[TenantDB]:
        async with AsyncSession(self.engine) as session:
            stmt = (
                select(TenantDB)
                .join(TenantMembershipDB)
                .where(
                    TenantMembershipDB.subject == subject,
                    TenantMembershipDB.revoked.is_(False),
                )
                .order_by(TenantDB.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_api_key(
        self,
        tenant_id: str,
        api_key_id: str,
        secret: str,
        roles: list[str],
        expires_at: datetime | None = None,
    ) -> APIKeyDB:
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        key = APIKeyDB(
            api_key_id=api_key_id,
            tenant_id=tenant_id,
            hashed_secret=hash_api_key_secret(secret),
            roles=roles,
            expires_at=expires_at,
        )
        async with AsyncSession(self.engine) as session:
            session.add(key)
            await session.commit()
            await session.refresh(key)
        return key

    async def get_tenant(self, tenant_id: str) -> TenantDB | None:
        async with AsyncSession(self.engine) as session:
            return await session.get(TenantDB, tenant_id)

    async def update_tenant(
        self,
        tenant_id: str,
        name: str | None = None,
        slug: str | None = None,
        status: str | None = None,
    ) -> TenantDB:
        async with AsyncSession(self.engine) as session:
            tenant = await session.get(TenantDB, tenant_id)
            if tenant is None:
                raise NotFoundError(f"Tenant not found: {tenant_id}")

            if slug is not None and slug != tenant.slug:
                existing = await self.get_tenant_by_slug(slug)
                if existing is not None and existing.tenant_id != tenant_id:
                    raise ValueError(f"Tenant slug already exists: {slug}")
                tenant.slug = slug

            if name is not None:
                tenant.name = name

            if status is not None:
                allowed = {"pending", "active", "suspended", "archived"}
                if status not in allowed:
                    raise ValueError(
                        f"Invalid tenant status: {status}. Allowed: {allowed}"
                    )
                tenant.status = status

            tenant.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(tenant)
            return tenant

    async def list_api_keys(self, tenant_id: str) -> list[APIKeyDB]:
        async with AsyncSession(self.engine) as session:
            stmt = select(APIKeyDB).where(APIKeyDB.tenant_id == tenant_id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def revoke_api_key(self, api_key_id: str, tenant_id: str) -> bool:
        async with AsyncSession(self.engine) as session:
            key = await session.get(APIKeyDB, api_key_id)
            if key is None or key.tenant_id != tenant_id:
                return False
            key.revoked = True
            await session.commit()
            return True

    async def list_memberships(self, tenant_id: str) -> list[TenantMembershipDB]:
        async with AsyncSession(self.engine) as session:
            stmt = select(TenantMembershipDB).where(
                TenantMembershipDB.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_membership(
        self, subject: str, tenant_id: str, role: str
    ) -> TenantMembershipDB:
        membership = TenantMembershipDB(
            membership_id=str(uuid.uuid4()),
            subject=subject,
            tenant_id=tenant_id,
            role=role,
        )
        async with AsyncSession(self.engine) as session:
            session.add(membership)
            await session.commit()
            await session.refresh(membership)
        return membership

    async def revoke_membership(self, membership_id: str, tenant_id: str) -> bool:
        async with AsyncSession(self.engine) as session:
            membership = await session.get(TenantMembershipDB, membership_id)
            if membership is None or membership.tenant_id != tenant_id:
                return False
            membership.revoked = True
            membership.updated_at = datetime.now(timezone.utc)
            await session.commit()
            return True
