from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from thebe_core.audit.service import AuditService
from thebe_core.config import settings
from thebe_core.creator.service import VERTICAL, upload_root
from thebe_core.creator.tables import BookDB, BookEditionDB, MindDB, SourceDocumentDB

SEED_AUTHOR_ID = "seed-author-mara"
SEED_BOOK_ID = "seed-book-manuscript-to-launch"
SEED_PAPERBACK_ID = "seed-edition-paperback"
SEED_EBOOK_ID = "seed-edition-ebook"
SEED_DOCUMENT_ID = "seed-document-excerpt"
SEED_MIND_ROW_ID = "seed-mind-mara"

SEED_CONTEXT = {
    "display_name": "Mara Ellison",
    "biography": "First-time-author advocate writing a practical publishing workflow from manuscript to launch.",
    "voice": "Practical, encouraging, specific, and careful with claims",
    "audience": "First-time authors preparing a completed manuscript for publication",
    "genres": "publishing, nonfiction",
    "rights": "all_rights_owned",
    "prohibited_topics": "guaranteed income, guaranteed sales",
    "preferred_terms": "manuscript, reader, publishing workflow, author approval, source material",
    "approval_policy": "Review all public-facing claims before publication",
    "publisher_name": "Ellison Press",
}


def _excerpt_text() -> str:
    path = Path(__file__).resolve().parents[2] / "verticals" / "creator_publishing" / "sample_excerpt.txt"
    return path.read_text(encoding="utf-8")


async def seed_creatortrust(
    audit: AuditService,
    tenant_id: str,
    *,
    reuse_author: bool = False,
) -> None:
    """Idempotent seed for the demo author, book, editions, and excerpt."""
    existing = await audit.get_customer(SEED_AUTHOR_ID, tenant_id)
    if existing is None:
        await audit.create_customer(
            customer_id=SEED_AUTHOR_ID,
            tenant_id=tenant_id,
            vertical=VERTICAL,
            name="Mara Ellison",
            slug="mara-ellison",
            status="active",
            context=SEED_CONTEXT,
        )
    elif reuse_author:
        await audit.update_customer(
            customer_id=SEED_AUTHOR_ID,
            tenant_id=tenant_id,
            name="Mara Ellison",
            status="active",
            context=SEED_CONTEXT,
        )

    async with AsyncSession(audit.engine) as session:
        mind = await session.get(MindDB, SEED_MIND_ROW_ID)
        if mind is None:
            session.add(
                MindDB(
                    id=SEED_MIND_ROW_ID,
                    tenant_id=tenant_id,
                    author_id=SEED_AUTHOR_ID,
                    mind_id=settings.MINDS_MIND_ID,
                    mind_email=settings.MINDS_MIND_EMAIL,
                    status="bound"
                    if settings.MINDS_API_BASE_URL and settings.MINDS_API_KEY
                    else "awaiting_credentials",
                    active_skills=["message", "generate_assets"],
                    memory_version="1",
                )
            )

        book = await session.get(BookDB, SEED_BOOK_ID)
        if book is None:
            session.add(
                BookDB(
                    id=SEED_BOOK_ID,
                    tenant_id=tenant_id,
                    author_id=SEED_AUTHOR_ID,
                    working_title="Manuscript to Launch",
                    final_title="Manuscript to Launch",
                    subtitle="Practical publishing workflow for first-time authors",
                    series_name=None,
                    description="A practical publishing workflow for first-time authors preparing a completed manuscript for publication.",
                    status="active",
                    publication_strategy="kdp_and_ingramspark",
                )
            )

        paperback = await session.get(BookEditionDB, SEED_PAPERBACK_ID)
        if paperback is None:
            session.add(
                BookEditionDB(
                    id=SEED_PAPERBACK_ID,
                    tenant_id=tenant_id,
                    book_id=SEED_BOOK_ID,
                    format="paperback",
                    isbn="9781234567897",
                    language="en",
                    trim_size="6x9",
                    page_count=220,
                    list_price=18.99,
                    currency="USD",
                    publication_date="2026-09-01",
                    platform_strategy={
                        "kdp": True,
                        "ingramspark": True,
                        "publisher_field": "Mara Ellison",
                    },
                    publishing_status="not_started",
                    proof_review_status="not_requested",
                )
            )

        ebook = await session.get(BookEditionDB, SEED_EBOOK_ID)
        if ebook is None:
            session.add(
                BookEditionDB(
                    id=SEED_EBOOK_ID,
                    tenant_id=tenant_id,
                    book_id=SEED_BOOK_ID,
                    format="ebook",
                    isbn="9781234567903",
                    language="en",
                    list_price=9.99,
                    currency="USD",
                    publication_date="2026-09-01",
                    platform_strategy={
                        "kdp": True,
                        "ingramspark": True,
                        "publisher_field": "Mara Ellison",
                    },
                    publishing_status="not_started",
                    proof_review_status="not_applicable",
                )
            )

        document = await session.get(SourceDocumentDB, SEED_DOCUMENT_ID)
        if document is None:
            excerpt = _excerpt_text()
            dest_dir = upload_root() / tenant_id / SEED_BOOK_ID
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"{SEED_DOCUMENT_ID}.txt"
            data = excerpt.encode("utf-8")
            dest.write_bytes(data)
            session.add(
                SourceDocumentDB(
                    id=SEED_DOCUMENT_ID,
                    tenant_id=tenant_id,
                    book_id=SEED_BOOK_ID,
                    file_uri=str(dest),
                    file_name="sample_excerpt.txt",
                    mime_type="text/plain",
                    sha256=hashlib.sha256(data).hexdigest(),
                    extracted_text=excerpt,
                    rights_declaration="all_rights_owned",
                    version=1,
                    uploaded_by="seed",
                )
            )
        await session.commit()
