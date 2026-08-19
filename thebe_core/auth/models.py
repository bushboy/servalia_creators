from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import DateTime
from sqlmodel import JSON, Column, Field, SQLModel, String

from thebe_core.config import settings


@dataclass
class TenantContext:
    """Security context extracted from an authenticated request."""

    tenant_id: str
    subject: str | None = None  # external user id, for OIDC tokens
    api_key_id: str | None = None  # for API-key callers
    roles: list[str] | None = None
    auth_method: str = "unknown"  # "bearer" | "api_key" | "dev"

    def has_role(self, role: str) -> bool:
        return self.roles is not None and role in self.roles


class TenantDB(SQLModel, table=True):
    """A tenant / customer organization."""

    __tablename__ = "tenants"

    tenant_id: str = Field(primary_key=True)
    name: str
    slug: str = Field(sa_column=Column(String(255), unique=True, index=True))
    status: str = "active"  # active | suspended | archived
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class TenantMembershipDB(SQLModel, table=True):
    """Maps an external identity provider subject to a local tenant and role."""

    __tablename__ = "tenant_memberships"

    membership_id: str = Field(primary_key=True)
    subject: str = Field(index=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    role: str
    revoked: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


class APIKeyDB(SQLModel, table=True):
    """Tenant-scoped API key for machine-to-machine access."""

    __tablename__ = "api_keys"

    api_key_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenants.tenant_id", index=True)
    hashed_secret: str = Field(sa_column=Column(String(255)))
    roles: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    expires_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )
    revoked: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )


    def verify_secret(self, secret: str) -> bool:
        if not self.hashed_secret:
            return False
        combined = _peppered_secret(secret)
        return bcrypt.checkpw(combined.encode(), self.hashed_secret.encode())


def _peppered_secret(secret: str) -> str:
    """Combine the configured pepper with the secret before hashing."""
    return f"{settings.API_KEY_PEPPER.get_secret_value()}:{secret}"


def hash_api_key_secret(secret: str) -> str:
    """Hash an API key secret for storage."""
    combined = _peppered_secret(secret)
    return bcrypt.hashpw(combined.encode(), bcrypt.gensalt()).decode()
