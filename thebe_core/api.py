from __future__ import annotations

import asyncio
import logging
import os
import re
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from thebe_core.api_responses import (
    ApiResponse,
    PaginationMeta,
    build_error,
    build_response,
)
from thebe_core.audit.service import AuditService
from thebe_core.auth.dependencies import RoleRequired, get_current_subject
from thebe_core.auth.exceptions import NotFoundError
from thebe_core.auth.models import TenantContext
from thebe_core.auth.service import AuthService
from thebe_core.config import settings
from thebe_core.creator.router import router as creator_router
from thebe_core.creator.seed import seed_creatortrust
from thebe_core.creator.service import CreatorService
from thebe_core.jobs import JobService
from thebe_core.models import (
    AuditEvent,
    QuestionCatalog,
    TimelineEvent,
)
from thebe_core.verticals.loader import VerticalLoader
from thebe_core.verticals.pack import VerticalPack

# ---------------------------------------------------------------------------
# Logging: structured JSON for production, with per-request redaction aware.
# ---------------------------------------------------------------------------


def _setup_logging() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)


_setup_logging()
logger = logging.getLogger("thebe.api")

HTTP_REQUESTS_TOTAL = Counter(
    "thebe_http_requests_total",
    "Total HTTP requests",
    ["method", "status"],
)


class CustomerContextUpdate(BaseModel):
    context: dict[str, Any]


class VerticalInfo(BaseModel):
    id: str
    name: str
    description: str


class TenantInfoResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    status: str
    roles: list[str]
    auth_method: str
    subject: str | None = None


class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    slug: str
    status: str
    created_at: datetime


class TenantUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    status: str | None = None


class TenantCreateRequest(BaseModel):
    name: str
    slug: str | None = None


class CustomerResponse(BaseModel):
    customer_id: str
    tenant_id: str
    vertical: str
    name: str
    slug: str | None = None
    status: str
    context: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class CustomerCreateRequest(BaseModel):
    vertical: str
    name: str
    slug: str | None = None
    context: dict[str, Any] = {}


class CustomerUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    status: str | None = None
    context: dict[str, Any] | None = None


class ApiKeyResponse(BaseModel):
    api_key_id: str
    tenant_id: str
    roles: list[str]
    expires_at: datetime | None
    revoked: bool
    created_at: datetime


class ApiKeyCreateRequest(BaseModel):
    api_key_id: str
    roles: list[str]
    expires_at: datetime | None = None


class ApiKeyCreateResponse(BaseModel):
    api_key_id: str
    secret: str


class TenantMembershipResponse(BaseModel):
    membership_id: str
    subject: str
    tenant_id: str
    role: str
    revoked: bool
    created_at: datetime


class TenantMembershipCreateRequest(BaseModel):
    subject: str
    role: str


class JobCreateRequest(BaseModel):
    job_type: str
    payload: dict[str, Any] = {}
    max_retries: int = 3


class JobResponse(BaseModel):
    job_id: str
    tenant_id: str
    job_type: str
    status: str
    retry_count: int
    max_retries: int
    last_error: str | None = None
    result: dict[str, Any] | None = None
    payload: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class SystemEventResponse(BaseModel):
    event_id: str
    event_type: str
    severity: str
    message: str
    occurred_at: datetime
    artifact_id: str | None = None
    link: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_vertical_packs() -> dict[str, VerticalPack]:
    root = Path(__file__).parents[1] / "verticals"
    packs: dict[str, VerticalPack] = {}
    if not root.exists():
        return packs

    for path in root.iterdir():
        if not path.is_dir():
            continue
        has_pack_files = any(
            (path / filename).exists()
            for filename in (
                "pack.yaml",
                "pack.yml",
                "onboarding_schema.json",
                "rules.yaml",
                "rules.json",
            )
        )
        if not has_pack_files:
            continue
        try:
            packs[path.name] = VerticalLoader.load(path)
        except Exception as exc:
            logger.warning("Failed to load vertical %s: %s", path.name, exc)
    return packs


def _rate_limit_key(request: Request) -> str:
    auth = (
        request.headers.get("authorization")
        or request.headers.get("x-api-key")
        or ""
    )
    if auth.lower().startswith("apikey "):
        parts = auth.split(" ", 1)[1].split(":", 1)
        return f"api:{parts[0]}"
    if request.client and request.client.host:
        return f"ip:{request.client.host}"
    return "ip:unknown"


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalize_slug(value: str) -> str:
    """Slugify a tenant name: lowercase, trim, collapse spaces into hyphens."""
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    if not slug:
        raise ValueError(f"Cannot derive slug from name: {value!r}")
    return slug


def _validate_slug(slug: str) -> None:
    """Validate a tenant slug is URL-safe and reasonable in length."""
    if len(slug) > 63:
        raise ValueError("Tenant slug must be 63 characters or fewer")
    if not SLUG_RE.match(slug):
        raise ValueError(
            "Tenant slug must be lowercase alphanumeric with single hyphens"
        )


def _get_pack(vertical: str) -> VerticalPack:
    pack = app.state.packs.get(vertical)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Vertical not found: {vertical}")
    return pack


async def _log_action(
    tenant_id: str,
    action: str,
    vertical: str,
    customer_id: str,
    input_snapshot: dict,
    output_snapshot: dict,
) -> None:
    event = AuditEvent(
        tenant_id=tenant_id,
        vertical=vertical,
        customer_id=customer_id,
        agent_id="api",
        action=action,
        input_snapshot=input_snapshot,
        output_snapshot=output_snapshot,
    )
    await app.state.audit.log_event(event)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request id (or forward the caller's) and echo it back."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-key rate limiter with swappable Redis (prod) and memory (dev) storage."""

    def __init__(self, app, rate_limit: str | None = None):
        super().__init__(app)
        self.item = parse(rate_limit or settings.RATE_LIMIT)
        storage: Any = MemoryStorage()
        if settings.REDIS_URL:
            try:
                from limits.storage import RedisStorage

                storage = RedisStorage(settings.REDIS_URL)
                logger.info("Rate limiting backed by Redis")
            except Exception as exc:
                logger.warning(
                    "REDIS_URL configured but Redis storage unavailable: %s", exc
                )
        self.limiter = MovingWindowRateLimiter(storage)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        key = _rate_limit_key(request)
        if not self.limiter.hit(self.item, key):
            logger.warning("Rate limit exceeded for key %s", key)
            return PlainTextResponse("Rate limit exceeded", status_code=429)

        return await call_next(request)


class LogRequestsMiddleware(BaseHTTPMiddleware):
    """Log every request and emit a Prometheus counter."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        request_id = getattr(request.state, "request_id", "n/a")

        logger.info(
            "%s %s - %s - %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            extra={"request_id": request_id},
        )
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, status=str(response.status_code)
        ).inc()
        return response


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    audit = AuditService(database_url)
    await audit.create_tables()
    auth = AuthService(audit.engine)

    packs = _load_vertical_packs()
    app.state.audit = audit
    app.state.auth_service = auth
    app.state.packs = packs
    app.state.job_service = JobService(audit, packs)
    app.state.creator = CreatorService(audit, packs)
    worker_task = asyncio.create_task(app.state.job_service.run())

    if os.environ.get("SEED_TEST_TENANT"):
        tenant = await auth.get_tenant("test-tenant")
        if tenant is None:
            await auth.create_tenant("test-tenant", "Test Tenant", "test-tenant")
            await auth.create_api_key(
                "test-tenant", "test-api-key", "test-secret", ["admin"]
            )
            oidc_test_sub = os.environ.get("SEED_OIDC_TEST_USER_SUB")
            if oidc_test_sub:
                await auth.create_membership(oidc_test_sub, "test-tenant", "admin")
        await seed_creatortrust(audit, "test-tenant")

    logger.info("Thebe Core API started with %d vertical packs", len(packs))
    yield
    app.state.job_service.stop()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    await app.state.audit.engine.dispose()


app = FastAPI(
    title="CreatorTrust API",
    description="Servalia governance core used by CreatorTrust.",
    version="0.3.0",
    lifespan=lifespan,
    docs_url=None if settings.DISABLE_DOCS else "/docs",
    redoc_url=None if settings.DISABLE_DOCS else "/redoc",
    openapi_url=None if settings.DISABLE_DOCS else "/openapi.json",
)

# CORS must be registered before auth/rate-limit middleware so preflight
# OPTIONS requests are answered before those layers run.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Middleware is applied in reverse order of registration; the outermost
# (last registered) is RequestIdMiddleware so downstream middleware can
# access request.state.request_id on the response path.
app.add_middleware(LogRequestsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIdMiddleware)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=400,
        content=build_error(
            message=str(exc),
            request_id=request_id,
            code="bad_request",
        ),
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=404,
        content=build_error(
            message=f"Not found: {exc}",
            request_id=request_id,
            code="not_found",
        ),
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=404,
        content=build_error(
            message=str(exc),
            request_id=request_id,
            code="not_found",
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    code = "error"
    if exc.status_code == 401:
        code = "unauthenticated"
    elif exc.status_code == 403:
        code = "forbidden"
    elif exc.status_code == 404:
        code = "not_found"
    elif exc.status_code == 429:
        code = "rate_limited"
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error(
            message=exc.detail,
            request_id=request_id,
            code=code,
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=build_error(
            message="Internal server error",
            request_id=request_id,
            code="internal_error",
        ),
    )

@app.get("/customers", response_model=list[CustomerResponse])
async def list_customers(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> list[CustomerResponse]:
    rows = await app.state.audit.list_customers(
        tenant_id=tenant_context.tenant_id,
        status=status,
        limit=limit,
    )
    return [CustomerResponse(**row.model_dump()) for row in rows]

@app.post("/customers", response_model=CustomerResponse, status_code=201)
async def create_customer_endpoint(
    payload: CustomerCreateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(RoleRequired(["operator", "admin"])),
) -> CustomerResponse:
    customer_id = str(uuid.uuid4())
    slug = payload.slug or _normalize_slug(payload.name)
    _validate_slug(slug)
    await app.state.audit.create_customer(
        customer_id=customer_id,
        tenant_id=tenant_context.tenant_id,
        vertical=payload.vertical,
        name=payload.name,
        slug=slug,
        status="draft",
        context=payload.context,
    )
    row = await app.state.audit.get_customer(
        customer_id=customer_id, tenant_id=tenant_context.tenant_id
    )
    assert row is not None
    return CustomerResponse(**row.model_dump())

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer_endpoint(
    customer_id: str,
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> CustomerResponse:
    row = await app.state.audit.get_customer(
        customer_id=customer_id, tenant_id=tenant_context.tenant_id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**row.model_dump())

@app.patch("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer_endpoint(
    customer_id: str,
    payload: CustomerUpdateRequest,
    tenant_context: TenantContext = Depends(RoleRequired(["operator", "admin"])),
) -> CustomerResponse:
    if payload.slug is not None:
        _validate_slug(payload.slug)
    row = await app.state.audit.update_customer(
        customer_id=customer_id,
        tenant_id=tenant_context.tenant_id,
        name=payload.name,
        slug=payload.slug,
        status=payload.status,
        context=payload.context,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**row.model_dump())

@app.get("/customers/{customer_id}/timeline", response_model=list[TimelineEvent])
async def get_customer_timeline(
    customer_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> list[TimelineEvent]:
    return await app.state.audit.get_customer_timeline(
        customer_id=customer_id,
        tenant_id=tenant_context.tenant_id,
        limit=limit,
    )

@app.patch("/customers/{customer_id}/context", response_model=CustomerResponse)
async def update_customer_context(
    customer_id: str,
    payload: CustomerContextUpdate,
    request: Request,
    tenant_context: TenantContext = Depends(RoleRequired(["operator", "admin"])),
) -> CustomerResponse:
    customer = await app.state.audit.get_customer(
        customer_id=customer_id, tenant_id=tenant_context.tenant_id
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    row = await app.state.audit.update_customer(
        customer_id=customer_id,
        tenant_id=tenant_context.tenant_id,
        context=payload.context,
    )
    await _log_action(
        tenant_id=tenant_context.tenant_id,
        action="update_customer_context",
        vertical=customer.vertical,
        customer_id=customer_id,
        input_snapshot={"context": payload.context},
        output_snapshot={"customer_id": customer_id},
    )
    return CustomerResponse(**row.model_dump())

@app.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job_endpoint(
    payload: JobCreateRequest,
    tenant_context: TenantContext = Depends(
        RoleRequired(["operator", "admin"])
    ),
) -> JobResponse:
    job = await app.state.job_service.create_job(
        tenant_id=tenant_context.tenant_id,
        job_type=payload.job_type,
        payload=payload.payload,
        max_retries=payload.max_retries,
    )
    return JobResponse(**job.model_dump())

@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs_endpoint(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> list[JobResponse]:
    rows = await app.state.job_service.list_jobs(
        tenant_id=tenant_context.tenant_id,
        status=status,
        limit=limit,
    )
    return [JobResponse(**row.model_dump()) for row in rows]

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_endpoint(
    job_id: str,
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> JobResponse:
    row = await app.state.job_service.get_job(job_id, tenant_context.tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**row.model_dump())

@app.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job_endpoint(
    job_id: str,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> JobResponse:
    row = await app.state.job_service.retry_job(job_id, tenant_context.tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found or not failed")
    return JobResponse(**row.model_dump())

@app.get("/audit", response_model=list[AuditEvent])
async def audit_query(
    customer_id: str | None = Query(default=None),
    vertical: str | None = Query(default=None),
    action: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> list[AuditEvent]:
    filters: dict[str, Any] = {}
    for key, value in (
        ("tenant_id", tenant_context.tenant_id),
        ("customer_id", customer_id),
        ("vertical", vertical),
        ("action", action),
        ("agent_id", agent_id),
    ):
        if value is not None:
            filters[key] = value
    return await app.state.audit.query_events(filters, limit=limit)

@app.get("/verticals", response_model=list[VerticalInfo])
async def list_verticals(
    request: Request,
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> list[VerticalInfo]:
    return [
        VerticalInfo(id=pack_id, name=pack.name, description=pack.description)
        for pack_id, pack in app.state.packs.items()
    ]

@app.get("/verticals/{vertical_id}/questions", response_model=QuestionCatalog)
async def get_question_catalog(
    vertical_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> QuestionCatalog:
    pack = _get_pack(vertical_id)
    catalog = pack.get_question_catalog()
    if catalog is None:
        raise HTTPException(
            status_code=404,
            detail=f"Question catalog not found for vertical: {vertical_id}",
        )
    return catalog

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        async with app.state.audit.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database not ready") from exc

@app.get(
    "/metrics",
    dependencies=[Depends(RoleRequired(["admin"]))] if settings.METRICS_REQUIRE_AUTH else [],
)
async def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/me", response_model=TenantInfoResponse)
async def me(
    tenant_context: TenantContext = Depends(
        RoleRequired(["viewer", "operator", "admin"])
    ),
) -> TenantInfoResponse:
    tenant = await app.state.auth_service.get_tenant(tenant_context.tenant_id)
    return TenantInfoResponse(
        tenant_id=tenant_context.tenant_id,
        name=tenant.name if tenant else "",
        slug=tenant.slug if tenant else "",
        status=tenant.status if tenant else "unknown",
        roles=tenant_context.roles or [],
        auth_method=tenant_context.auth_method,
        subject=tenant_context.subject,
    )

@app.get("/me/tenants", response_model=ApiResponse)
async def list_my_tenants(
    request: Request,
    subject: str = Depends(get_current_subject),
) -> dict[str, Any]:
    rows = await app.state.auth_service.get_tenants_for_subject(subject)
    tenants = [TenantResponse(**row.model_dump()) for row in rows]
    return build_response(
        tenants,
        request_id=getattr(request.state, "request_id", None),
        pagination=PaginationMeta(
            page=1,
            page_size=len(tenants),
            total=len(tenants),
        ),
    )

@app.post("/tenants", response_model=ApiResponse, status_code=201)
async def create_tenant_endpoint(
    payload: TenantCreateRequest,
    request: Request,
    subject: str = Depends(get_current_subject),
) -> dict[str, Any]:
    """Create a new tenant and make the authenticated subject its admin.

    This is the controlled entry point for tenant onboarding. In a real
    deployment this should be gated by an invite code, verified domain or
    admin approval; for now it requires only an authenticated OIDC user.
    """
    slug = _normalize_slug(payload.slug) if payload.slug else _normalize_slug(
        payload.name
    )
    _validate_slug(slug)

    existing = await app.state.auth_service.get_tenant_by_slug(slug)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant_id = str(uuid.uuid4())
    tenant = await app.state.auth_service.create_tenant(
        tenant_id=tenant_id,
        name=payload.name,
        slug=slug,
    )
    await app.state.auth_service.create_membership(subject, tenant_id, "admin")

    return build_response(
        TenantResponse(**tenant.model_dump()).model_dump(),
        request_id=getattr(request.state, "request_id", None),
    )


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


admin_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(RoleRequired(["admin"]))],
)

@admin_router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> list[ApiKeyResponse]:
    rows = await app.state.auth_service.list_api_keys(tenant_context.tenant_id)
    return [ApiKeyResponse(**row.model_dump()) for row in rows]

@admin_router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> ApiKeyCreateResponse:
    # Keep the generated secret short enough that the peppered value stays
    # within bcrypt's 72-byte input limit.
    secret = secrets.token_urlsafe(16)
    await app.state.auth_service.create_api_key(
        tenant_id=tenant_context.tenant_id,
        api_key_id=payload.api_key_id,
        secret=secret,
        roles=payload.roles,
        expires_at=payload.expires_at,
    )
    return ApiKeyCreateResponse(api_key_id=payload.api_key_id, secret=secret)

@admin_router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> dict[str, bool]:
    ok = await app.state.auth_service.revoke_api_key(
        api_key_id=api_key_id, tenant_id=tenant_context.tenant_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"revoked": True}

@admin_router.get("/members", response_model=list[TenantMembershipResponse])
async def list_members(
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> list[TenantMembershipResponse]:
    rows = await app.state.auth_service.list_memberships(tenant_context.tenant_id)
    return [TenantMembershipResponse(**row.model_dump()) for row in rows]

@admin_router.post("/members", response_model=TenantMembershipResponse)
async def create_member(
    payload: TenantMembershipCreateRequest,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> TenantMembershipResponse:
    row = await app.state.auth_service.create_membership(
        subject=payload.subject,
        tenant_id=tenant_context.tenant_id,
        role=payload.role,
    )
    return TenantMembershipResponse(**row.model_dump())

@admin_router.delete("/members/{membership_id}")
async def revoke_member(
    membership_id: str,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> dict[str, bool]:
    ok = await app.state.auth_service.revoke_membership(
        membership_id=membership_id, tenant_id=tenant_context.tenant_id
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Membership not found")
    return {"revoked": True}

@admin_router.get("/system/events", response_model=list[SystemEventResponse])
async def list_system_events(
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> list[SystemEventResponse]:
    events = await app.state.job_service.get_system_events(tenant_context.tenant_id)
    return [SystemEventResponse(**event) for event in events]

@admin_router.get("/tenant", response_model=TenantResponse)
async def get_tenant(
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> TenantResponse:
    row = await app.state.auth_service.get_tenant(tenant_context.tenant_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(**row.model_dump())

@admin_router.patch("/tenant", response_model=TenantResponse)
async def update_tenant(
    payload: TenantUpdateRequest,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> TenantResponse:
    if payload.slug is not None:
        _validate_slug(payload.slug)
    row = await app.state.auth_service.update_tenant(
        tenant_id=tenant_context.tenant_id,
        name=payload.name,
        slug=payload.slug,
        status=payload.status,
    )
    return TenantResponse(**row.model_dump())

app.include_router(admin_router)
app.include_router(creator_router)
