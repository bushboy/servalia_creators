from __future__ import annotations

from typing import Any

from thebe_core.audit.service import AuditService
from thebe_core.audit.store import JobDB
from thebe_core.creator.publishing import IngramSparkDestinationAdapter, KdpDestinationAdapter
from thebe_core.creator.service import CreatorService
from thebe_core.models import AuditEvent
from thebe_core.verticals.pack import VerticalPack


async def execute_mind_message(
    audit: AuditService,
    packs: dict[str, VerticalPack],
    job: JobDB,
) -> dict[str, Any]:
    service = CreatorService(audit, packs)
    payload = job.payload or {}
    author_id = payload["author_id"]
    mind_id, reply, source = await service.message_mind(
        job.tenant_id, author_id, payload["message"]
    )
    return {
        "author_id": author_id,
        "mind_id": mind_id,
        "reply": reply,
        "source": source,
    }


async def execute_generate_assets(
    audit: AuditService,
    packs: dict[str, VerticalPack],
    job: JobDB,
) -> dict[str, Any]:
    service = CreatorService(audit, packs)
    payload = job.payload or {}
    tenant_id = job.tenant_id
    book_id = payload["book_id"]
    document_id = payload["source_document_id"]
    book = await service.get_book(tenant_id, book_id)
    author = await audit.get_customer(book.author_id, tenant_id)
    document = await service.get_document(tenant_id, document_id)
    if author is None:
        raise KeyError(book.author_id)
    assets = await service.generate_asset_payloads(author, book, document)
    created = await service.persist_generated_assets(tenant_id, book, document, assets)
    return {"asset_ids": [row.id for row in created], "count": len(created)}


async def execute_build_package(
    audit: AuditService,
    packs: dict[str, VerticalPack],
    job: JobDB,
) -> dict[str, Any]:
    service = CreatorService(audit, packs)
    payload = job.payload or {}
    tenant_id = job.tenant_id
    edition_id = payload["edition_id"]
    destination = payload["destination"]
    edition = await service.get_edition(tenant_id, edition_id)
    book = await service.get_book(tenant_id, edition.book_id)
    author = await audit.get_customer(book.author_id, tenant_id)
    if author is None:
        raise KeyError(book.author_id)
    assets = await service.list_assets(tenant_id, book.id)
    if not service.required_assets_approved(assets):
        raise ValueError("Approve the book description before building a package")
    excerpt = await service.latest_document(tenant_id, book.id)
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
    await audit.log_event(
        AuditEvent(
            tenant_id=tenant_id,
            vertical="creator_publishing",
            customer_id=book.author_id,
            action="package_built",
            input_snapshot={"edition_id": edition_id, "destination": destination},
            output_snapshot={"filename": package.filename},
        )
    )
    return {
        "filename": package.filename,
        "path": str(package.path),
        "validation": package.validation.as_dict(),
    }
