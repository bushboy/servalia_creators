from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

from thebe_core.auth.dependencies import RoleRequired
from thebe_core.auth.models import TenantContext
from thebe_core.creator.publishing import (
    IngramSparkDestinationAdapter,
    KdpDestinationAdapter,
)
from thebe_core.creator.schemas import (
    AssetDecisionRequest,
    AssetResponse,
    AssetReviseRequest,
    AuthorCreateRequest,
    AuthorResponse,
    AuthorUpdateRequest,
    BookCreateRequest,
    BookResponse,
    BookUpdateRequest,
    CampaignCreateRequest,
    CampaignResponse,
    DocumentResponse,
    EditionCreateRequest,
    EditionResponse,
    EditionUpdateRequest,
    GenerateAssetsRequest,
    GenerateAssetsResponse,
    MindMessageRequest,
    MindMessageResponse,
    MindStatus,
    PublishingStatusUpdate,
)
from thebe_core.creator.service import (
    CreatorService,
    asset_response,
    book_response,
    document_response,
    edition_response,
)
from thebe_core.minds.client import MindsApiError, MindsNotConfigured
from thebe_core.models import AuditEvent

Viewer = RoleRequired(["viewer", "operator", "admin"])
Operator = RoleRequired(["operator", "admin"])

router = APIRouter(tags=["creatortrust"])


def _service(request: Request) -> CreatorService:
    svc = getattr(request.app.state, "creator", None)
    if svc is None:
        svc = CreatorService(request.app.state.audit, request.app.state.packs)
        request.app.state.creator = svc
    return svc


def _http(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=f"Not found: {exc}")
    if isinstance(exc, MindsNotConfigured):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, MindsApiError):
        status = 504 if exc.code == "timeout" or exc.status in {0, 408, 504} else 502
        return HTTPException(status_code=status, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    raise exc


@router.get("/authors", response_model=list[AuthorResponse])
async def list_authors(
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> list[AuthorResponse]:
    return await _service(request).list_authors(tenant_context.tenant_id)


@router.post("/authors", response_model=AuthorResponse, status_code=201)
async def create_author(
    payload: AuthorCreateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> AuthorResponse:
    return await _service(request).create_author(
        tenant_context.tenant_id, payload.name, payload.context
    )


@router.get("/authors/{author_id}", response_model=AuthorResponse)
async def get_author(
    author_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> AuthorResponse:
    try:
        return await _service(request).get_author(tenant_context.tenant_id, author_id)
    except KeyError as exc:
        raise _http(exc) from exc


@router.patch("/authors/{author_id}", response_model=AuthorResponse)
async def patch_author(
    author_id: str,
    payload: AuthorUpdateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> AuthorResponse:
    try:
        return await _service(request).update_author(
            tenant_context.tenant_id,
            author_id,
            payload.name,
            payload.status,
            payload.context,
        )
    except KeyError as exc:
        raise _http(exc) from exc


@router.get("/authors/{author_id}/mind/status", response_model=MindStatus)
async def mind_status(
    author_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> MindStatus:
    try:
        return await _service(request).mind_status(tenant_context.tenant_id, author_id)
    except KeyError as exc:
        raise _http(exc) from exc


@router.post("/authors/{author_id}/mind/message", response_model=MindMessageResponse)
async def mind_message(
    author_id: str,
    payload: MindMessageRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> MindMessageResponse:
    """Enqueue a Mind turn. Poll GET /jobs/{job_id} for the reply.

    Builder replies often take 1–2 minutes. Holding the HTTP connection
    trips the frontend proxy (504) even when the API later succeeds.
    """
    service = _service(request)
    try:
        await service.get_author(tenant_context.tenant_id, author_id)
        if not service.minds.configured:
            raise MindsNotConfigured(
                "Minds is not configured. Set MINDS_API_KEY on the API."
            )
        job = await request.app.state.job_service.create_job(
            tenant_context.tenant_id,
            "mind_message",
            {"author_id": author_id, "message": payload.message},
            max_retries=1,
        )
    except (KeyError, MindsNotConfigured, ValueError) as exc:
        raise _http(exc) from exc
    return MindMessageResponse(
        job_id=job.job_id, status=job.status, author_id=author_id
    )


@router.post("/books", response_model=BookResponse, status_code=201)
async def create_book(
    payload: BookCreateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> BookResponse:
    try:
        row = await _service(request).create_book(
            tenant_context.tenant_id, payload.model_dump()
        )
    except KeyError as exc:
        raise _http(exc) from exc
    return book_response(row)


@router.get("/books", response_model=list[BookResponse])
async def list_books(
    request: Request,
    author_id: str | None = Query(default=None),
    tenant_context: TenantContext = Depends(Viewer),
) -> list[BookResponse]:
    rows = await _service(request).list_books(tenant_context.tenant_id, author_id)
    return [book_response(row) for row in rows]


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> BookResponse:
    try:
        return book_response(await _service(request).get_book(tenant_context.tenant_id, book_id))
    except KeyError as exc:
        raise _http(exc) from exc


@router.patch("/books/{book_id}", response_model=BookResponse)
async def patch_book(
    book_id: str,
    payload: BookUpdateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> BookResponse:
    try:
        row = await _service(request).update_book(
            tenant_context.tenant_id,
            book_id,
            payload.model_dump(exclude_unset=True),
        )
    except KeyError as exc:
        raise _http(exc) from exc
    return book_response(row)


@router.get("/books/{book_id}/editions", response_model=list[EditionResponse])
async def list_editions(
    book_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> list[EditionResponse]:
    try:
        rows = await _service(request).list_editions(tenant_context.tenant_id, book_id)
    except KeyError as exc:
        raise _http(exc) from exc
    return [edition_response(row) for row in rows]


@router.post("/books/{book_id}/editions", response_model=EditionResponse, status_code=201)
async def create_edition(
    book_id: str,
    payload: EditionCreateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> EditionResponse:
    try:
        row = await _service(request).create_edition(
            tenant_context.tenant_id, book_id, payload.model_dump()
        )
    except KeyError as exc:
        raise _http(exc) from exc
    return edition_response(row)


@router.patch("/editions/{edition_id}", response_model=EditionResponse)
async def patch_edition(
    edition_id: str,
    payload: EditionUpdateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> EditionResponse:
    try:
        row = await _service(request).update_edition(
            tenant_context.tenant_id,
            edition_id,
            payload.model_dump(exclude_unset=True),
        )
    except KeyError as exc:
        raise _http(exc) from exc
    return edition_response(row)


@router.post("/books/{book_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    book_id: str,
    request: Request,
    file: UploadFile = File(...),
    rights_declaration: str = Form(default="all_rights_owned"),
    tenant_context: TenantContext = Depends(Operator),
) -> DocumentResponse:
    content = await file.read()
    try:
        row = await _service(request).save_document(
            tenant_context.tenant_id,
            book_id,
            file.filename or "excerpt.txt",
            content,
            rights_declaration,
            tenant_context.subject,
        )
    except (KeyError, ValueError) as exc:
        raise _http(exc) from exc
    return document_response(row)


@router.get("/books/{book_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    book_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> list[DocumentResponse]:
    try:
        rows = await _service(request).list_documents(tenant_context.tenant_id, book_id)
    except KeyError as exc:
        raise _http(exc) from exc
    return [document_response(row) for row in rows]


@router.post("/books/{book_id}/generate-assets", response_model=GenerateAssetsResponse)
async def generate_assets(
    book_id: str,
    payload: GenerateAssetsRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> GenerateAssetsResponse:
    service = _service(request)
    try:
        document_id = payload.source_document_id
        if not document_id:
            latest = await service.latest_document(tenant_context.tenant_id, book_id)
            if latest is None:
                raise ValueError("Upload an excerpt before generating assets")
            document_id = latest.id
        await service.get_document(tenant_context.tenant_id, document_id)
        job = await request.app.state.job_service.create_job(
            tenant_context.tenant_id,
            "generate_assets",
            {"book_id": book_id, "source_document_id": document_id},
            max_retries=1,
        )
    except (KeyError, ValueError) as exc:
        raise _http(exc) from exc
    return GenerateAssetsResponse(job_id=job.job_id, status=job.status)


@router.get("/books/{book_id}/assets", response_model=list[AssetResponse])
async def list_assets(
    book_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> list[AssetResponse]:
    try:
        rows = await _service(request).current_assets(tenant_context.tenant_id, book_id)
    except KeyError as exc:
        raise _http(exc) from exc
    return [asset_response(row) for row in rows]


@router.post("/assets/{asset_id}/evaluate", response_model=AssetResponse)
async def evaluate_asset(
    asset_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> AssetResponse:
    try:
        row = await _service(request).evaluate_asset(tenant_context.tenant_id, asset_id)
    except KeyError as exc:
        raise _http(exc) from exc
    return asset_response(row)


@router.post("/assets/{asset_id}/approve", response_model=AssetResponse)
async def approve_asset(
    asset_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> AssetResponse:
    try:
        row = await _service(request).approve_asset(tenant_context.tenant_id, asset_id)
    except (KeyError, ValueError) as exc:
        raise _http(exc) from exc
    return asset_response(row)


@router.post("/assets/{asset_id}/reject", response_model=AssetResponse)
async def reject_asset(
    asset_id: str,
    payload: AssetDecisionRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> AssetResponse:
    try:
        row = await _service(request).reject_asset(
            tenant_context.tenant_id, asset_id, payload.note
        )
    except KeyError as exc:
        raise _http(exc) from exc
    return asset_response(row)


@router.post("/assets/{asset_id}/revise", response_model=AssetResponse)
async def revise_asset(
    asset_id: str,
    payload: AssetReviseRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> AssetResponse:
    try:
        row = await _service(request).revise_asset(
            tenant_context.tenant_id, asset_id, payload.correction
        )
    except (KeyError, ValueError) as exc:
        raise _http(exc) from exc
    return asset_response(row)


async def _package_response(
    request: Request,
    tenant_context: TenantContext,
    edition_id: str,
    destination: str,
) -> FileResponse:
    service = _service(request)
    try:
        edition = await service.get_edition(tenant_context.tenant_id, edition_id)
        book = await service.get_book(tenant_context.tenant_id, edition.book_id)
        author = await request.app.state.audit.get_customer(
            book.author_id, tenant_context.tenant_id
        )
        if author is None:
            raise KeyError(book.author_id)
        assets = await service.list_assets(tenant_context.tenant_id, book.id)
        if not service.required_assets_approved(assets):
            raise ValueError("Approve the book description before building a package")
        excerpt = await service.latest_document(tenant_context.tenant_id, book.id)
        adapter = (
            KdpDestinationAdapter()
            if destination == "kdp"
            else IngramSparkDestinationAdapter()
        )
        package = await adapter.build_package(
            book,
            edition,
            author_name=author.name,
            author_context=author.context or {},
            excerpt=excerpt,
            pack=service.pack(),
        )
        if not package.validation.ok:
            raise ValueError(
                "; ".join(issue.message for issue in package.validation.issues)
            )
        await request.app.state.audit.log_event(
            AuditEvent(
                tenant_id=tenant_context.tenant_id,
                vertical="creator_publishing",
                customer_id=book.author_id,
                action="package_built",
                input_snapshot={"edition_id": edition_id, "destination": destination},
                output_snapshot={"filename": package.filename},
            )
        )
    except (KeyError, ValueError) as exc:
        raise _http(exc) from exc
    return FileResponse(
        path=package.path,
        filename=package.filename,
        media_type="application/zip",
    )


@router.post("/editions/{edition_id}/packages/kdp")
async def package_kdp(
    edition_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> FileResponse:
    return await _package_response(request, tenant_context, edition_id, "kdp")


@router.post("/editions/{edition_id}/packages/ingramspark")
async def package_ingram(
    edition_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> FileResponse:
    return await _package_response(request, tenant_context, edition_id, "ingramspark")


@router.get("/editions/{edition_id}/publishing-status", response_model=EditionResponse)
async def publishing_status(
    edition_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> EditionResponse:
    try:
        return edition_response(
            await _service(request).get_edition(tenant_context.tenant_id, edition_id)
        )
    except KeyError as exc:
        raise _http(exc) from exc


@router.post("/editions/{edition_id}/publishing-status", response_model=EditionResponse)
async def update_publishing_status(
    edition_id: str,
    payload: PublishingStatusUpdate,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> EditionResponse:
    try:
        row = await _service(request).update_edition(
            tenant_context.tenant_id,
            edition_id,
            payload.model_dump(exclude_unset=True),
        )
    except KeyError as exc:
        raise _http(exc) from exc
    return edition_response(row)


@router.post("/books/{book_id}/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    book_id: str,
    payload: CampaignCreateRequest,
    request: Request,
    tenant_context: TenantContext = Depends(Operator),
) -> CampaignResponse:
    service = _service(request)
    try:
        campaign = await service.create_campaign(
            tenant_context.tenant_id, book_id, payload.model_dump()
        )
        return await service.get_campaign(tenant_context.tenant_id, campaign.id)
    except KeyError as exc:
        raise _http(exc) from exc


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> CampaignResponse:
    try:
        return await _service(request).get_campaign(tenant_context.tenant_id, campaign_id)
    except KeyError as exc:
        raise _http(exc) from exc


@router.get("/books/{book_id}/campaigns/latest", response_model=CampaignResponse | None)
async def latest_campaign(
    book_id: str,
    request: Request,
    tenant_context: TenantContext = Depends(Viewer),
) -> CampaignResponse | None:
    try:
        await _service(request).get_book(tenant_context.tenant_id, book_id)
    except KeyError as exc:
        raise _http(exc) from exc
    return await _service(request).latest_campaign(tenant_context.tenant_id, book_id)


@router.get("/books/{book_id}/audit")
async def book_audit(
    book_id: str,
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_context: TenantContext = Depends(Viewer),
) -> list[AuditEvent]:
    try:
        return await _service(request).book_audit(
            tenant_context.tenant_id, book_id, limit=limit
        )
    except KeyError as exc:
        raise _http(exc) from exc


@router.post("/admin/demo-reset")
async def demo_reset(
    request: Request,
    tenant_context: TenantContext = Depends(RoleRequired(["admin"])),
) -> dict[str, Any]:
    await _service(request).reset_demo(tenant_context.tenant_id)
    return {"status": "ok", "tenant_id": tenant_context.tenant_id}
