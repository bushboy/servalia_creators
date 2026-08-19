"""Text predicates for creator_publishing rules.

Each predicate returns True when the asset is safe (engine PASS).
False becomes FAIL, then the evaluate wrapper maps selected rules to PARTIAL (Review).
"""

from __future__ import annotations

import re

from thebe_core.models import EntityContext

GUARANTEE_RE = re.compile(
    r"\b(guarantees?|guaranteed|will double|every new author will)\b",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"
)
MARKETPLACE_PUBLISHERS = {
    "amazon",
    "kdp",
    "amazon kdp",
    "kindle",
    "ingramspark",
    "ingram",
    "amazon.com",
}

OWNED_RIGHTS = {"all_rights_owned", "owned", "licensed_with_permission"}


def _attrs(ctx: EntityContext) -> dict:
    return ctx.attributes or {}


def _asset_text(ctx: EntityContext) -> str:
    attrs = _attrs(ctx)
    asset = attrs.get("asset") or {}
    return str(asset.get("content") or attrs.get("text") or "")


def _author_context(ctx: EntityContext) -> dict:
    attrs = _attrs(ctx)
    return attrs.get("author") or attrs.get("context") or {}


def rights_declared(ctx: EntityContext) -> bool:
    rights = str(_author_context(ctx).get("rights") or "").strip().lower()
    if not rights or rights == "unknown":
        return False
    return rights in OWNED_RIGHTS


def no_undeclared_pii(ctx: EntityContext) -> bool:
    text = _asset_text(ctx)
    author = _author_context(ctx)
    declared = bool(author.get("pii_declared") or author.get("named_third_parties_declared"))
    if declared:
        return True
    if EMAIL_RE.search(text) or PHONE_RE.search(text):
        return False
    if re.search(r"\b(my friend [A-Z][a-z]+|Dr\. [A-Z][a-z]+)\b", text):
        return False
    return True


def no_unsupported_guarantee(ctx: EntityContext) -> bool:
    return GUARANTEE_RE.search(_asset_text(ctx)) is None


def voice_aligned(ctx: EntityContext) -> bool:
    text = _asset_text(ctx).lower()
    author = _author_context(ctx)
    raw = author.get("prohibited_topics") or []
    if isinstance(raw, str):
        topics = [part.strip() for part in raw.split(",") if part.strip()]
    else:
        topics = [str(part).strip() for part in raw if str(part).strip()]
    for topic in topics:
        if topic.lower() in text:
            return False
    preferred = author.get("preferred_terms") or []
    if isinstance(preferred, str):
        terms = [part.strip() for part in preferred.split(",") if part.strip()]
    else:
        terms = [str(part).strip() for part in preferred if str(part).strip()]
    if terms and not any(term.lower() in text for term in terms):
        return False
    return True


def platform_metadata_ok(ctx: EntityContext) -> bool:
    edition = _attrs(ctx).get("edition") or {}
    author = _author_context(ctx)
    fmt = str(edition.get("format") or "").lower()
    isbn = str(edition.get("isbn") or "").strip()
    if fmt in {"paperback", "hardcover", "print"} and not isbn:
        return False
    publisher = str(
        (edition.get("platform_strategy") or {}).get("publisher_field")
        or author.get("publisher_name")
        or author.get("display_name")
        or ""
    ).strip()
    if not publisher:
        return False
    if publisher.lower() in MARKETPLACE_PUBLISHERS:
        return False
    allowed = {
        str(author.get("display_name") or "").strip().lower(),
        str(author.get("publisher_name") or "").strip().lower(),
        str(_attrs(ctx).get("author_name") or "").strip().lower(),
    }
    allowed.discard("")
    if allowed and publisher.lower() not in allowed:
        return False
    return True


def creator_predicates() -> dict:
    return {
        "rights_declared": rights_declared,
        "no_undeclared_pii": no_undeclared_pii,
        "no_unsupported_guarantee": no_unsupported_guarantee,
        "voice_aligned": voice_aligned,
        "platform_metadata_ok": platform_metadata_ok,
    }
