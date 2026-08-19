from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from thebe_core.audit.service import AuditService
from thebe_core.audit.store import CustomerDB
from thebe_core.config import settings
from thebe_core.creator.compose import ASSET_SPECS, compose_assets
from thebe_core.creator.predicates import creator_predicates
from thebe_core.creator.schemas import (
    AssetResponse,
    AuthorResponse,
    BookResponse,
    CampaignResponse,
    CampaignTaskResponse,
    DocumentResponse,
    EditionResponse,
    MindStatus,
)
from thebe_core.creator.tables import (
    AssetDB,
    BookDB,
    BookEditionDB,
    CampaignDB,
    CampaignTaskDB,
    MindDB,
    SourceDocumentDB,
)
from thebe_core.minds.client import MindsApiError, MindsClient
from thebe_core.models import AuditEvent, EntityContext, EvaluationResult
from thebe_core.policy.engine import PolicyEngine
from thebe_core.verticals.pack import VerticalPack

VERTICAL = "creator_publishing"
REVIEW_RULES = {"CREATOR-CLAIM-001", "CREATOR-VOICE-001"}
ALLOWED_UPLOAD_SUFFIXES = {".txt", ".md"}
logger = logging.getLogger("thebe.creator")


def upload_root() -> Path:
    return Path(settings.UPLOAD_DIR)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def author_response(row: CustomerDB, mind: MindDB | None, configured: bool) -> AuthorResponse:
    mind_status = None
    if mind is not None:
        mind_status = MindStatus(
            mind_row_id=mind.id,
            mind_id=mind.mind_id,
            mind_email=mind.mind_email,
            status=mind.status,
            last_interaction_at=mind.last_interaction_at,
            memory_version=mind.memory_version,
            configured=configured,
        )
    return AuthorResponse(
        author_id=row.customer_id,
        customer_id=row.customer_id,
        tenant_id=row.tenant_id or "",
        name=row.name,
        status=row.status,
        vertical=row.vertical,
        context=row.context or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        mind=mind_status,
    )


def book_response(row: BookDB) -> BookResponse:
    return BookResponse.model_validate(row.model_dump())


def edition_response(row: BookEditionDB) -> EditionResponse:
    return EditionResponse.model_validate(row.model_dump())


def document_response(row: SourceDocumentDB) -> DocumentResponse:
    return DocumentResponse.model_validate(row.model_dump())


def asset_response(row: AssetDB) -> AssetResponse:
    return AssetResponse.model_validate(row.model_dump())


class CreatorService:
    def __init__(self, audit: AuditService, packs: dict[str, VerticalPack]) -> None:
        self.audit = audit
        self.packs = packs
        self.minds = MindsClient()

    def pack(self) -> VerticalPack:
        pack = self.packs.get(VERTICAL)
        if pack is None:
            raise KeyError(VERTICAL)
        return pack

    async def _audit(
        self,
        *,
        tenant_id: str,
        author_id: str,
        action: str,
        input_snapshot: dict[str, Any] | None = None,
        output_snapshot: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> None:
        await self.audit.log_event(
            AuditEvent(
                tenant_id=tenant_id,
                vertical=VERTICAL,
                customer_id=author_id,
                agent_id=agent_id,
                action=action,
                input_snapshot=input_snapshot or {},
                output_snapshot=output_snapshot or {},
            )
        )

    async def get_mind(self, tenant_id: str, author_id: str) -> MindDB | None:
        async with AsyncSession(self.audit.engine) as session:
            result = await session.execute(
                select(MindDB).where(
                    MindDB.tenant_id == tenant_id,
                    MindDB.author_id == author_id,
                )
            )
            return result.scalars().first()

    async def list_authors(self, tenant_id: str) -> list[AuthorResponse]:
        rows = await self.audit.list_customers(tenant_id)
        authors = [r for r in rows if r.vertical == VERTICAL]
        out: list[AuthorResponse] = []
        for row in authors:
            mind = await self.get_mind(tenant_id, row.customer_id)
            out.append(author_response(row, mind, self.minds.configured))
        return out

    async def get_author(self, tenant_id: str, author_id: str) -> AuthorResponse:
        row = await self.audit.get_customer(author_id, tenant_id)
        if row is None or row.vertical != VERTICAL:
            raise KeyError(author_id)
        mind = await self.get_mind(tenant_id, author_id)
        return author_response(row, mind, self.minds.configured)

    async def create_author(
        self,
        tenant_id: str,
        name: str,
        context: dict[str, Any],
    ) -> AuthorResponse:
        author_id = str(uuid.uuid4())
        await self.audit.create_customer(
            customer_id=author_id,
            tenant_id=tenant_id,
            vertical=VERTICAL,
            name=name,
            slug=None,
            status="active",
            context=context,
        )
        await self._bind_default_mind(tenant_id, author_id)
        await self._audit(
            tenant_id=tenant_id,
            author_id=author_id,
            action="author_created",
            output_snapshot={"name": name},
        )
        return await self.get_author(tenant_id, author_id)

    async def update_author(
        self,
        tenant_id: str,
        author_id: str,
        name: str | None,
        status: str | None,
        context: dict[str, Any] | None,
    ) -> AuthorResponse:
        row = await self.audit.update_customer(
            customer_id=author_id,
            tenant_id=tenant_id,
            name=name,
            status=status,
            context=context,
        )
        if row is None or row.vertical != VERTICAL:
            raise KeyError(author_id)
        await self._audit(
            tenant_id=tenant_id,
            author_id=author_id,
            action="author_updated",
            input_snapshot={"context_keys": list((context or {}).keys())},
        )
        return await self.get_author(tenant_id, author_id)

    async def _bind_default_mind(self, tenant_id: str, author_id: str) -> MindDB:
        existing = await self.get_mind(tenant_id, author_id)
        if existing is not None:
            return existing
        mind = MindDB(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            author_id=author_id,
            mind_id=settings.MINDS_MIND_ID,
            mind_email=settings.MINDS_MIND_EMAIL,
            status="bound" if self.minds.configured else "awaiting_credentials",
            active_skills=["message", "generate_assets"],
            memory_version="1",
        )
        async with AsyncSession(self.audit.engine) as session:
            session.add(mind)
            await session.commit()
            await session.refresh(mind)
        return mind

    async def mind_status(self, tenant_id: str, author_id: str) -> MindStatus:
        await self.get_author(tenant_id, author_id)
        mind = await self._bind_default_mind(tenant_id, author_id)
        return MindStatus(
            mind_row_id=mind.id,
            mind_id=mind.mind_id,
            mind_email=mind.mind_email,
            status=mind.status,
            last_interaction_at=mind.last_interaction_at,
            memory_version=mind.memory_version,
            configured=self.minds.configured,
        )

    async def message_mind(
        self, tenant_id: str, author_id: str, text: str
    ) -> tuple[str, str, str]:
        author = await self.get_author(tenant_id, author_id)
        mind = await self._bind_default_mind(tenant_id, author_id)
        result = await self.minds.message(
            mind.mind_id,
            text,
            metadata={"author_id": author_id, "author_name": author.name},
        )
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(MindDB, mind.id)
            if row is not None:
                row.last_interaction_at = _now()
                row.status = "active"
                await session.commit()
        await self._audit(
            tenant_id=tenant_id,
            author_id=author_id,
            action="mind_message",
            input_snapshot={"message": text},
            output_snapshot={"reply": result["reply"]},
            agent_id=mind.mind_id,
        )
        return mind.mind_id, result["reply"], "minds"

    async def list_books(self, tenant_id: str, author_id: str | None = None) -> list[BookDB]:
        async with AsyncSession(self.audit.engine) as session:
            stmt = select(BookDB).where(BookDB.tenant_id == tenant_id)
            if author_id:
                stmt = stmt.where(BookDB.author_id == author_id)
            stmt = stmt.order_by(BookDB.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_book(self, tenant_id: str, book_id: str) -> BookDB:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(BookDB, book_id)
            if row is None or row.tenant_id != tenant_id:
                raise KeyError(book_id)
            return row

    async def create_book(self, tenant_id: str, payload: dict[str, Any]) -> BookDB:
        await self.get_author(tenant_id, payload["author_id"])
        book = BookDB(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            author_id=payload["author_id"],
            working_title=payload["working_title"],
            final_title=payload.get("final_title"),
            subtitle=payload.get("subtitle"),
            series_name=payload.get("series_name"),
            description=payload.get("description") or "",
            publication_strategy=payload.get("publication_strategy") or "kdp_and_ingramspark",
        )
        async with AsyncSession(self.audit.engine) as session:
            session.add(book)
            await session.commit()
            await session.refresh(book)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="book_created",
            output_snapshot={"book_id": book.id, "title": book.working_title},
        )
        return book

    async def update_book(self, tenant_id: str, book_id: str, fields: dict[str, Any]) -> BookDB:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(BookDB, book_id)
            if row is None or row.tenant_id != tenant_id:
                raise KeyError(book_id)
            for key, value in fields.items():
                if value is not None:
                    setattr(row, key, value)
            row.updated_at = _now()
            await session.commit()
            await session.refresh(row)
            return row

    async def list_editions(self, tenant_id: str, book_id: str) -> list[BookEditionDB]:
        await self.get_book(tenant_id, book_id)
        async with AsyncSession(self.audit.engine) as session:
            result = await session.execute(
                select(BookEditionDB)
                .where(BookEditionDB.tenant_id == tenant_id, BookEditionDB.book_id == book_id)
                .order_by(BookEditionDB.created_at.asc())
            )
            return list(result.scalars().all())

    async def get_edition(self, tenant_id: str, edition_id: str) -> BookEditionDB:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(BookEditionDB, edition_id)
            if row is None or row.tenant_id != tenant_id:
                raise KeyError(edition_id)
            return row

    async def create_edition(
        self, tenant_id: str, book_id: str, payload: dict[str, Any]
    ) -> BookEditionDB:
        book = await self.get_book(tenant_id, book_id)
        edition = BookEditionDB(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            book_id=book_id,
            **payload,
        )
        async with AsyncSession(self.audit.engine) as session:
            session.add(edition)
            await session.commit()
            await session.refresh(edition)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="edition_created",
            output_snapshot={"edition_id": edition.id, "format": edition.format},
        )
        return edition

    async def update_edition(
        self, tenant_id: str, edition_id: str, fields: dict[str, Any]
    ) -> BookEditionDB:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(BookEditionDB, edition_id)
            if row is None or row.tenant_id != tenant_id:
                raise KeyError(edition_id)
            for key, value in fields.items():
                if value is not None:
                    setattr(row, key, value)
            row.updated_at = _now()
            await session.commit()
            await session.refresh(row)
            book = await session.get(BookDB, row.book_id)
            author_id = book.author_id if book else ""
        if author_id:
            await self._audit(
                tenant_id=tenant_id,
                author_id=author_id,
                action="edition_updated",
                output_snapshot={"edition_id": edition_id},
            )
        return row

    async def save_document(
        self,
        tenant_id: str,
        book_id: str,
        filename: str,
        content: bytes,
        rights_declaration: str,
        uploaded_by: str | None,
    ) -> SourceDocumentDB:
        book = await self.get_book(tenant_id, book_id)
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_UPLOAD_SUFFIXES:
            raise ValueError("Only .txt and .md excerpts are accepted")
        text = content.decode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        doc_id = str(uuid.uuid4())
        dest_dir = upload_root() / tenant_id / book_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{doc_id}{suffix}"
        dest.write_bytes(content)
        mime = "text/markdown" if suffix == ".md" else "text/plain"
        async with AsyncSession(self.audit.engine) as session:
            existing = await session.execute(
                select(SourceDocumentDB)
                .where(
                    SourceDocumentDB.tenant_id == tenant_id,
                    SourceDocumentDB.book_id == book_id,
                )
                .order_by(SourceDocumentDB.version.desc())
            )
            latest = existing.scalars().first()
            version = (latest.version + 1) if latest else 1
            row = SourceDocumentDB(
                id=doc_id,
                tenant_id=tenant_id,
                book_id=book_id,
                file_uri=str(dest),
                file_name=filename,
                mime_type=mime,
                sha256=digest,
                extracted_text=text,
                rights_declaration=rights_declaration or "unknown",
                version=version,
                uploaded_by=uploaded_by,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="document_uploaded",
            output_snapshot={"document_id": row.id, "sha256": digest, "version": version},
        )
        return row

    async def list_documents(self, tenant_id: str, book_id: str) -> list[SourceDocumentDB]:
        await self.get_book(tenant_id, book_id)
        async with AsyncSession(self.audit.engine) as session:
            result = await session.execute(
                select(SourceDocumentDB)
                .where(
                    SourceDocumentDB.tenant_id == tenant_id,
                    SourceDocumentDB.book_id == book_id,
                )
                .order_by(SourceDocumentDB.created_at.desc())
            )
            return list(result.scalars().all())

    async def latest_document(self, tenant_id: str, book_id: str) -> SourceDocumentDB | None:
        docs = await self.list_documents(tenant_id, book_id)
        return docs[0] if docs else None

    async def get_document(self, tenant_id: str, document_id: str) -> SourceDocumentDB:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(SourceDocumentDB, document_id)
            if row is None or row.tenant_id != tenant_id:
                raise KeyError(document_id)
            return row

    async def list_assets(self, tenant_id: str, book_id: str) -> list[AssetDB]:
        await self.get_book(tenant_id, book_id)
        async with AsyncSession(self.audit.engine) as session:
            result = await session.execute(
                select(AssetDB)
                .where(AssetDB.tenant_id == tenant_id, AssetDB.book_id == book_id)
                .order_by(AssetDB.created_at.desc())
            )
            return list(result.scalars().all())

    async def current_assets(self, tenant_id: str, book_id: str) -> list[AssetDB]:
        rows = await self.list_assets(tenant_id, book_id)
        latest: dict[str, AssetDB] = {}
        for row in rows:
            if row.type not in latest:
                latest[row.type] = row
        return [latest[spec["type"]] for spec in ASSET_SPECS if spec["type"] in latest]

    async def get_asset(self, tenant_id: str, asset_id: str) -> AssetDB:
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(AssetDB, asset_id)
            if row is None or row.tenant_id != tenant_id:
                raise KeyError(asset_id)
            return row

    async def persist_generated_assets(
        self,
        tenant_id: str,
        book: BookDB,
        document: SourceDocumentDB,
        payloads: list[dict[str, Any]],
        *,
        parent_asset_id: str | None = None,
        applied_preference: bool = False,
        correction: str | None = None,
    ) -> list[AssetDB]:
        created: list[AssetDB] = []
        async with AsyncSession(self.audit.engine) as session:
            for payload in payloads:
                row = AssetDB(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    book_id=book.id,
                    source_document_id=document.id,
                    parent_asset_id=parent_asset_id,
                    type=payload["type"],
                    platform=payload.get("platform") or "kdp",
                    content=payload.get("content") or "",
                    source_references=payload.get("source_references") or [],
                    assumptions=payload.get("assumptions") or [],
                    call_to_action=payload.get("call_to_action") or "",
                    risk_notes=payload.get("risk_notes") or [],
                    governance_status="pending",
                    approval_status="draft",
                    author_correction=correction,
                    applied_preference=applied_preference,
                )
                session.add(row)
                created.append(row)
            await session.commit()
            for row in created:
                await session.refresh(row)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="assets_generated",
            output_snapshot={"book_id": book.id, "count": len(created)},
        )
        return created

    async def generate_asset_payloads(
        self,
        author: CustomerDB,
        book: BookDB,
        document: SourceDocumentDB,
        *,
        correction: str | None = None,
        asset_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        context = author.context or {}
        request = {
            "task": "generate_assets",
            "book": {
                "title": book.final_title or book.working_title,
                "subtitle": book.subtitle,
            },
            "author": {
                "name": author.name,
                "voice": context.get("voice"),
                "audience": context.get("audience"),
            },
            "excerpt": document.extracted_text,
            "source_document_id": document.id,
            "correction": correction,
            "asset_types": asset_types
            or [spec["type"] for spec in ASSET_SPECS],
        }
        mind = await self.get_mind(author.tenant_id or "", author.customer_id)
        if self.minds.configured and mind is not None:
            try:
                return await self.minds.generate_assets(mind.mind_id, request)
            except (ValueError, MindsApiError) as exc:
                logger.warning(
                    "Mind did not return structured assets (%s); using local composition",
                    exc,
                )
        return compose_assets(
            title=book.final_title or book.working_title,
            excerpt=document.extracted_text,
            author_name=author.name,
            voice=str(context.get("voice") or ""),
            audience=str(context.get("audience") or ""),
            preferred_terms=str(context.get("preferred_terms") or "reader"),
            correction=correction,
            asset_types=asset_types,
        )

    def _map_governance(self, result: EvaluationResult, context: EntityContext) -> EvaluationResult:
        edition = context.attributes.get("edition") or {}
        isbn = str(edition.get("isbn") or "").strip()
        fmt = str(edition.get("format") or "").lower()
        isbn_required_missing = fmt in {"paperback", "hardcover", "print"} and not isbn
        mapped = []
        for rule in result.rule_results:
            status = rule.status
            if status == "FAIL" and rule.rule_id in REVIEW_RULES:
                status = "PARTIAL"
            if (
                status == "FAIL"
                and rule.rule_id == "CREATOR-PLATFORM-001"
                and not isbn_required_missing
            ):
                status = "PARTIAL"
            mapped.append(rule.model_copy(update={"status": status}))
        result.rule_results = mapped
        result.violations = [
            v
            for v in result.violations
            if any(r.rule_id == v.rule_id and r.status in {"FAIL", "PARTIAL"} for r in mapped)
        ]
        for rule in mapped:
            if rule.status in {"FAIL", "PARTIAL"}:
                if not any(v.rule_id == rule.rule_id for v in result.violations):
                    from thebe_core.models import Violation

                    result.violations.append(
                        Violation(
                            rule_id=rule.rule_id,
                            control_key=rule.control_key,
                            obligation_key=rule.obligation_key,
                            description=rule.description,
                            severity=rule.severity,
                            recommended_actions=rule.recommended_actions,
                            source_fields=rule.source_fields,
                            evidence_ids=rule.evidence_ids,
                        )
                    )
        result.required_actions = list(
            dict.fromkeys(
                action
                for rule in mapped
                if rule.status in {"FAIL", "PARTIAL"}
                for action in rule.recommended_actions
            )
        )
        result.entity_type = "asset"
        return result

    def governance_label(self, result: EvaluationResult) -> str:
        if any(r.status == "FAIL" for r in result.rule_results):
            return "block"
        if any(r.status == "PARTIAL" for r in result.rule_results):
            return "review"
        return "allow"

    async def evaluate_asset(
        self, tenant_id: str, asset_id: str, edition_id: str | None = None
    ) -> AssetDB:
        asset = await self.get_asset(tenant_id, asset_id)
        book = await self.get_book(tenant_id, asset.book_id)
        author = await self.audit.get_customer(book.author_id, tenant_id)
        if author is None:
            raise KeyError(book.author_id)
        editions = await self.list_editions(tenant_id, book.id)
        edition = None
        if edition_id:
            edition = await self.get_edition(tenant_id, edition_id)
        elif editions:
            edition = next((e for e in editions if e.format == "paperback"), editions[0])
        edition_payload = edition.model_dump() if edition else {}
        context = EntityContext(
            entity_type="asset",
            attributes={
                "author": author.context or {},
                "author_name": author.name,
                "context": author.context or {},
                "asset": {"content": asset.content, "type": asset.type, "platform": asset.platform},
                "text": asset.content,
                "edition": edition_payload,
                "book": {"title": book.final_title or book.working_title},
            },
        )
        engine = PolicyEngine(predicates=creator_predicates())
        result = engine.evaluate(context, self.pack().get_rule_pack())
        result = self._map_governance(result, context)
        label = self.governance_label(result)
        dumped = result.model_dump(mode="json")
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(AssetDB, asset_id)
            row.evaluation = dumped
            row.governance_status = label
            await session.commit()
            await session.refresh(row)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="asset_evaluated",
            input_snapshot={"asset_id": asset_id},
            output_snapshot={"governance_status": label, "evaluation_id": result.evaluation_id},
        )
        await self.audit.persist_evaluation(
            evaluation_id=result.evaluation_id,
            tenant_id=tenant_id,
            customer_id=book.author_id,
            vertical=VERTICAL,
            entity_type="asset",
            score=result.score,
            rule_results=dumped.get("rule_results") or [],
            violations=dumped.get("violations") or [],
            required_actions=result.required_actions,
        )
        return row

    async def approve_asset(self, tenant_id: str, asset_id: str) -> AssetDB:
        asset = await self.get_asset(tenant_id, asset_id)
        if asset.governance_status == "block":
            raise ValueError("Blocked assets cannot be approved until they are revised")
        if asset.governance_status == "pending":
            asset = await self.evaluate_asset(tenant_id, asset_id)
            if asset.governance_status == "block":
                raise ValueError("Blocked assets cannot be approved until they are revised")
        book = await self.get_book(tenant_id, asset.book_id)
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(AssetDB, asset_id)
            row.approval_status = "approved"
            await session.commit()
            await session.refresh(row)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="asset_approved",
            output_snapshot={"asset_id": asset_id, "type": row.type},
        )
        return row

    async def reject_asset(self, tenant_id: str, asset_id: str, note: str | None) -> AssetDB:
        asset = await self.get_asset(tenant_id, asset_id)
        book = await self.get_book(tenant_id, asset.book_id)
        async with AsyncSession(self.audit.engine) as session:
            row = await session.get(AssetDB, asset_id)
            row.approval_status = "rejected"
            row.author_correction = note
            await session.commit()
            await session.refresh(row)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="asset_rejected",
            input_snapshot={"note": note},
            output_snapshot={"asset_id": asset_id, "type": row.type},
        )
        return row

    async def revise_asset(self, tenant_id: str, asset_id: str, correction: str) -> AssetDB:
        asset = await self.get_asset(tenant_id, asset_id)
        book = await self.get_book(tenant_id, asset.book_id)
        author = await self.audit.get_customer(book.author_id, tenant_id)
        if author is None:
            raise KeyError(book.author_id)
        document_id = asset.source_document_id
        if not document_id:
            raise ValueError("Asset has no source document to revise from")
        document = await self.get_document(tenant_id, document_id)
        payloads = await self.generate_asset_payloads(
            author,
            book,
            document,
            correction=correction,
            asset_types=[asset.type],
        )
        created = await self.persist_generated_assets(
            tenant_id,
            book,
            document,
            payloads,
            parent_asset_id=asset.id,
            applied_preference=True,
            correction=correction,
        )
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="asset_revised",
            input_snapshot={"parent_asset_id": asset.id, "correction": correction},
            output_snapshot={"asset_id": created[0].id, "type": created[0].type},
        )
        return created[0]

    def required_assets_approved(self, assets: list[AssetDB]) -> bool:
        latest = {row.type: row for row in reversed(assets)}
        description = latest.get("description")
        if description is None:
            return False
        return description.approval_status == "approved" and description.governance_status != "block"

    async def create_campaign(
        self, tenant_id: str, book_id: str, payload: dict[str, Any]
    ) -> CampaignDB:
        book = await self.get_book(tenant_id, book_id)
        assets = await self.current_assets(tenant_id, book_id)
        approved = [a for a in assets if a.approval_status == "approved"]
        campaign = CampaignDB(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            book_id=book_id,
            campaign_type=payload.get("campaign_type") or "launch",
            launch_date=payload.get("launch_date"),
            timezone=payload.get("timezone") or "UTC",
            status="planned",
        )
        phase_plan = [
            ("newsletter", "email", "pre-launch"),
            ("social_post", "social", "launch_week"),
            ("podcast_pitch", "podcast", "launch_week"),
            ("video_script", "video", "post-launch"),
            ("description", "kdp", "pre-launch"),
        ]
        by_type = {a.type: a for a in approved}
        async with AsyncSession(self.audit.engine) as session:
            session.add(campaign)
            await session.flush()
            for asset_type, channel, phase in phase_plan:
                asset = by_type.get(asset_type)
                session.add(
                    CampaignTaskDB(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        campaign_id=campaign.id,
                        asset_id=asset.id if asset else None,
                        channel=channel,
                        phase=phase,
                        approval_status="approved" if asset else "pending",
                        execution_status="not_started",
                    )
                )
            await session.commit()
            await session.refresh(campaign)
        await self._audit(
            tenant_id=tenant_id,
            author_id=book.author_id,
            action="campaign_created",
            output_snapshot={"campaign_id": campaign.id},
        )
        return campaign

    async def get_campaign(self, tenant_id: str, campaign_id: str) -> CampaignResponse:
        async with AsyncSession(self.audit.engine) as session:
            campaign = await session.get(CampaignDB, campaign_id)
            if campaign is None or campaign.tenant_id != tenant_id:
                raise KeyError(campaign_id)
            result = await session.execute(
                select(CampaignTaskDB).where(CampaignTaskDB.campaign_id == campaign_id)
            )
            tasks = list(result.scalars().all())
        return CampaignResponse(
            **campaign.model_dump(),
            tasks=[CampaignTaskResponse.model_validate(t.model_dump()) for t in tasks],
        )

    async def latest_campaign(self, tenant_id: str, book_id: str) -> CampaignResponse | None:
        async with AsyncSession(self.audit.engine) as session:
            result = await session.execute(
                select(CampaignDB)
                .where(CampaignDB.tenant_id == tenant_id, CampaignDB.book_id == book_id)
                .order_by(CampaignDB.created_at.desc())
                .limit(1)
            )
            campaign = result.scalars().first()
        if campaign is None:
            return None
        return await self.get_campaign(tenant_id, campaign.id)

    async def book_audit(self, tenant_id: str, book_id: str, limit: int = 100):
        book = await self.get_book(tenant_id, book_id)
        return await self.audit.query_events(
            {
                "tenant_id": tenant_id,
                "customer_id": book.author_id,
                "vertical": VERTICAL,
            },
            limit=limit,
        )

    async def reset_demo(self, tenant_id: str) -> None:
        from thebe_core.creator.seed import SEED_AUTHOR_ID, seed_creatortrust

        async with AsyncSession(self.audit.engine) as session:
            books = list(
                (
                    await session.execute(
                        select(BookDB).where(BookDB.tenant_id == tenant_id)
                    )
                ).scalars().all()
            )
            book_ids = [b.id for b in books]
            if book_ids:
                campaigns = list(
                    (
                        await session.execute(
                            select(CampaignDB).where(CampaignDB.book_id.in_(book_ids))
                        )
                    ).scalars().all()
                )
                campaign_ids = [c.id for c in campaigns]
                if campaign_ids:
                    await session.execute(
                        delete(CampaignTaskDB).where(
                            CampaignTaskDB.campaign_id.in_(campaign_ids)
                        )
                    )
                await session.execute(
                    delete(CampaignDB).where(CampaignDB.book_id.in_(book_ids))
                )
                await session.execute(
                    delete(AssetDB).where(AssetDB.book_id.in_(book_ids))
                )
                await session.execute(
                    delete(SourceDocumentDB).where(SourceDocumentDB.book_id.in_(book_ids))
                )
                await session.execute(
                    delete(BookEditionDB).where(BookEditionDB.book_id.in_(book_ids))
                )
                await session.execute(delete(BookDB).where(BookDB.id.in_(book_ids)))
            await session.execute(
                delete(MindDB).where(
                    MindDB.tenant_id == tenant_id,
                    MindDB.author_id == SEED_AUTHOR_ID,
                )
            )
            await session.commit()
        existing = await self.audit.get_customer(SEED_AUTHOR_ID, tenant_id)
        if existing is None:
            await seed_creatortrust(self.audit, tenant_id)
        else:
            await seed_creatortrust(self.audit, tenant_id, reuse_author=True)
        await self._audit(
            tenant_id=tenant_id,
            author_id=SEED_AUTHOR_ID,
            action="demo_reset",
            output_snapshot={"tenant_id": tenant_id},
        )
