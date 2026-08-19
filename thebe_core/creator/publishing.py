from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from jinja2 import Environment

from thebe_core.config import settings
from thebe_core.creator.tables import BookDB, BookEditionDB, SourceDocumentDB
from thebe_core.verticals.pack import VerticalPack

MARKETPLACE_NAMES = {"amazon", "kdp", "amazon kdp", "kindle", "ingram", "ingramspark"}


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str


@dataclass
class ValidationResult:
    destination: str
    ok: bool
    issues: list[ValidationIssue]

    def as_dict(self) -> dict[str, Any]:
        return {
            "destination": self.destination,
            "ok": self.ok,
            "issues": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in self.issues
            ],
        }


@dataclass
class PublishingPackage:
    filename: str
    path: Path
    validation: ValidationResult


@dataclass
class DestinationStatus:
    destination: str
    publishing_status: str
    proof_review_status: str


class PublishingDestination(Protocol):
    destination_name: str

    async def validate(self, book: BookDB, edition: BookEditionDB, author_name: str, author_context: dict) -> ValidationResult: ...

    async def build_package(
        self,
        book: BookDB,
        edition: BookEditionDB,
        *,
        author_name: str,
        author_context: dict[str, Any],
        excerpt: SourceDocumentDB | None,
        pack: VerticalPack,
    ) -> PublishingPackage: ...

    async def get_status(self, edition: BookEditionDB) -> DestinationStatus: ...


def _packages_root() -> Path:
    return Path(settings.PACKAGE_DIR)


def _render(template_name: str, pack: VerticalPack, **values: Any) -> str:
    templates = pack.get_templates()
    template = templates.get(template_name)
    if template is None:
        return f"# {template_name}\n\nTemplate missing.\n"
    env = Environment(trim_blocks=True, lstrip_blocks=True)
    return env.from_string(template.content).render(**values)


def _publisher_allowed(publisher: str, author_name: str, author_context: dict[str, Any]) -> bool:
    value = publisher.strip()
    if not value:
        return False
    if value.lower() in MARKETPLACE_NAMES:
        return False
    allowed = {
        author_name.strip().lower(),
        str(author_context.get("display_name") or "").strip().lower(),
        str(author_context.get("publisher_name") or "").strip().lower(),
    }
    allowed.discard("")
    return value.lower() in allowed


def _write_zip(filename: str, files: dict[str, str | bytes]) -> Path:
    dest_dir = _packages_root()
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in files.items():
            data = payload.encode("utf-8") if isinstance(payload, str) else payload
            zf.writestr(name, data)
    return path


class KdpDestinationAdapter:
    destination_name = "kdp"

    async def validate(
        self,
        book: BookDB,
        edition: BookEditionDB,
        author_name: str,
        author_context: dict[str, Any],
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        publisher = str(
            (edition.platform_strategy or {}).get("publisher_field")
            or author_context.get("publisher_name")
            or author_context.get("display_name")
            or author_name
        )
        if not _publisher_allowed(publisher, author_name, author_context):
            issues.append(
                ValidationIssue(
                    "kdp_publisher_field",
                    "KDP publisher field must be the author or imprint name only.",
                    "error",
                )
            )
        if not (book.final_title or book.working_title):
            issues.append(ValidationIssue("title", "Title is required.", "error"))
        return ValidationResult(self.destination_name, ok=not issues, issues=issues)

    async def build_package(
        self,
        book: BookDB,
        edition: BookEditionDB,
        *,
        author_name: str,
        author_context: dict[str, Any],
        excerpt: SourceDocumentDB | None,
        pack: VerticalPack,
    ) -> PublishingPackage:
        validation = await self.validate(book, edition, author_name, author_context)
        metadata = {
            "destination": "kdp",
            "title": book.final_title or book.working_title,
            "subtitle": book.subtitle,
            "author": author_name,
            "publisher": (edition.platform_strategy or {}).get("publisher_field")
            or author_context.get("publisher_name")
            or author_name,
            "format": edition.format,
            "isbn": edition.isbn,
            "language": edition.language,
            "list_price": edition.list_price,
            "currency": edition.currency,
            "publication_date": edition.publication_date,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        }
        values = {
            "book": book,
            "edition": edition,
            "author_name": author_name,
        }
        files: dict[str, str | bytes] = {
            "metadata.json": json.dumps(metadata, indent=2),
            "checklist.md": _render("kdp_checklist", pack, **values),
            "validation-report.json": json.dumps(validation.as_dict(), indent=2),
            "SUBMIT.md": _render("submit_kdp", pack, **values),
        }
        if excerpt is not None:
            files["excerpt.txt"] = excerpt.extracted_text
        filename = f"creatortrust-kdp-{edition.format}.zip"
        if edition.format == "paperback":
            filename = "creatortrust-kdp-paperback.zip"
        path = _write_zip(filename, files)
        return PublishingPackage(filename=filename, path=path, validation=validation)

    async def get_status(self, edition: BookEditionDB) -> DestinationStatus:
        return DestinationStatus(
            destination=self.destination_name,
            publishing_status=edition.publishing_status,
            proof_review_status=edition.proof_review_status,
        )


class IngramSparkDestinationAdapter:
    destination_name = "ingramspark"

    async def validate(
        self,
        book: BookDB,
        edition: BookEditionDB,
        author_name: str,
        author_context: dict[str, Any],
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        fmt = edition.format.lower()
        if fmt in {"paperback", "hardcover", "print"} and not (edition.isbn or "").strip():
            issues.append(
                ValidationIssue(
                    "ingram_isbn",
                    "Ingram print editions require an ISBN.",
                    "error",
                )
            )
        if not edition.format:
            issues.append(ValidationIssue("ingram_format", "Format is required.", "error"))
        return ValidationResult(self.destination_name, ok=not issues, issues=issues)

    async def build_package(
        self,
        book: BookDB,
        edition: BookEditionDB,
        *,
        author_name: str,
        author_context: dict[str, Any],
        excerpt: SourceDocumentDB | None,
        pack: VerticalPack,
    ) -> PublishingPackage:
        validation = await self.validate(book, edition, author_name, author_context)
        metadata = {
            "destination": "ingramspark",
            "title": book.final_title or book.working_title,
            "subtitle": book.subtitle,
            "author": author_name,
            "format": edition.format,
            "isbn": edition.isbn,
            "language": edition.language,
            "trim_size": edition.trim_size,
            "page_count": edition.page_count,
            "list_price": edition.list_price,
            "currency": edition.currency,
            "publication_date": edition.publication_date,
            "proof_review_status": edition.proof_review_status,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        }
        values = {
            "book": book,
            "edition": edition,
            "author_name": author_name,
        }
        files: dict[str, str | bytes] = {
            "metadata.json": json.dumps(metadata, indent=2),
            "checklist.md": _render("ingramspark_checklist", pack, **values),
            "validation-report.json": json.dumps(validation.as_dict(), indent=2),
            "SUBMIT.md": _render("submit_ingramspark", pack, **values),
        }
        if excerpt is not None:
            files["excerpt.txt"] = excerpt.extracted_text
        filename = f"creatortrust-ingramspark-{edition.format}.zip"
        if edition.format == "paperback":
            filename = "creatortrust-ingramspark-paperback.zip"
        path = _write_zip(filename, files)
        return PublishingPackage(filename=filename, path=path, validation=validation)

    async def get_status(self, edition: BookEditionDB) -> DestinationStatus:
        return DestinationStatus(
            destination=self.destination_name,
            publishing_status=edition.publishing_status,
            proof_review_status=edition.proof_review_status,
        )
