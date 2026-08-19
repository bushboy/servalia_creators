from __future__ import annotations

import os
from logging.config import fileConfig
from urllib.parse import urlparse, urlunparse

from sqlalchemy import engine_from_config, pool

from alembic import context


def _to_sync_database_url(url: str) -> str:
    """Return a synchronous SQLAlchemy URL suitable for Alembic migrations.

    The application uses an async driver (asyncpg). Alembic runs migrations
    synchronously, so we swap it for the matching synchronous driver.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme
    if scheme.startswith("postgresql+asyncpg"):
        scheme = scheme.replace("asyncpg", "psycopg2")
    elif scheme == "postgresql":
        scheme = "postgresql+psycopg2"
    elif scheme.startswith("sqlite"):
        # SQLite URLs are already synchronous from Alembic's perspective.
        return url
    return urlunparse(parsed._replace(scheme=scheme))

# Import all table modules so SQLModel's shared metadata is fully populated.
from thebe_core.audit.store import (
    AuditEventDB,
    CustomerDB,
    EvaluationDB,
)
from thebe_core.auth.models import APIKeyDB, TenantDB, TenantMembershipDB
from thebe_core.creator import tables as _creator_tables  # noqa: F401
from sqlmodel import SQLModel

# this is the Alembic Config object
config = context.config

# Resolve the DB URL from the environment (same as the app) so that we do not
# bake credentials into alembic.ini. Alembic uses a synchronous driver, so map
# async application URLs to their synchronous equivalents.
config.set_main_option(
    "sqlalchemy.url",
    _to_sync_database_url(
        os.environ.get("DATABASE_URL", "sqlite:///thebe.db")
    ),
)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
