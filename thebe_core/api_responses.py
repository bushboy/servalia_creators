"""Standard API response envelope and pagination metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    request_id: str | None = None
    version: str = "0.2.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int
    total: int
    next_cursor: str | None = None


class ErrorDetail(BaseModel):
    code: str | None = None
    message: str
    details: dict[str, Any] | None = None


class ApiResponse(BaseModel):
    data: Any | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
    error: ErrorDetail | None = None


def build_response(
    data: Any,
    request_id: str | None = None,
    pagination: PaginationMeta | None = None,
    error: ErrorDetail | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable envelope for API responses."""
    body: dict[str, Any] = {
        "data": data,
        "meta": ResponseMeta(request_id=request_id).model_dump(mode="json"),
    }
    if pagination is not None:
        body["pagination"] = pagination.model_dump(mode="json")
    if error is not None:
        body["error"] = error.model_dump(mode="json")
    return body


def build_error(
    message: str,
    request_id: str | None = None,
    code: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable error envelope."""
    error = ErrorDetail(message=message)
    if code is not None:
        error.code = code
    if details is not None:
        error.details = details
    return build_response(data=None, request_id=request_id, error=error)
