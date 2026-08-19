from __future__ import annotations

import asyncio
import json
import re
import time
from html.parser import HTMLParser

import httpx

from thebe_core.config import settings

DEFAULT_BASE_URL = "https://api.build.hellominds.ai"
DEFAULT_ALIAS = "creatortrust"

# Official @animocabrands/minds-client-lib: 1 = human, 0/2 = Mind.
_HUMAN_SENDER = 1
_MIND_SENDERS = {0, 2}


class MindsNotConfigured(RuntimeError):
    """Raised when the Builder API is not configured on the server."""


class MindsApiError(RuntimeError):
    """Raised when the Builder API returns an error or a reply times out."""

    def __init__(self, message: str, *, status: int = 0, code: str = "http_error") -> None:
        super().__init__(message)
        self.status = status
        self.code = code


def normalize_base_url(url: str | None) -> str:
    """Strip trailing slash and a duplicated /v1 suffix. Paths always start with /v1/."""
    value = (url or DEFAULT_BASE_URL).strip()
    if not value:
        value = DEFAULT_BASE_URL
    value = value.rstrip("/")
    if value.endswith("/v1"):
        value = value[:-3].rstrip("/")
    return value or DEFAULT_BASE_URL


def _sender_type(row: dict[str, Any]) -> int | None:
    raw = row.get("senderType", row.get("partyType"))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


_BLOCK_TAGS = {
    "p",
    "div",
    "section",
    "article",
    "header",
    "footer",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "pre",
    "ul",
    "ol",
    "table",
}
_BREAK_TAGS = {"br", "hr"}
_LIST_ITEM_TAGS = {"li"}


class _HTMLToText(HTMLParser):
    """Turn Mind HTML (p, br, lists) into plain text with line breaks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _BREAK_TAGS:
            self._parts.append("\n")
        elif tag in _LIST_ITEM_TAGS:
            self._parts.append("\n• ")
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _BLOCK_TAGS or tag in _LIST_ITEM_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        raw = re.sub(r"[ \t]+\n", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r"[ \t]{2,}", " ", raw)
        return raw.strip()


def looks_like_html(value: str) -> bool:
    return bool(re.search(r"<[a-zA-Z][^>]*>", value))


def format_mind_reply(value: str) -> str:
    """Builder messageText is often HTML. Store and display readable text."""
    stripped = (value or "").strip()
    if not stripped or not looks_like_html(stripped):
        return stripped
    parser = _HTMLToText()
    try:
        parser.feed(stripped)
        parser.close()
    except Exception:
        return stripped
    return parser.text() or stripped


def _message_text(row: dict[str, Any]) -> str:
    for key in (
        "messageText",
        "html",
        "messageHtml",
        "content",
        "message",
        "text",
        "reply",
    ):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return format_mind_reply(value)
    return ""


def _as_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("items", "messages", "history"):
            value = data.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _is_mind_reply(
    row: dict[str, Any],
    *,
    sent_text: str,
    after_fingerprint: str | None,
    alias: str,
) -> bool:
    text = _message_text(row).strip()
    if not text:
        return False
    if text == sent_text.strip():
        return False
    row_alias = row.get("alias")
    if isinstance(row_alias, str) and row_alias and row_alias != alias:
        return False
    sender = _sender_type(row)
    if sender == _HUMAN_SENDER or row.get("senderName") == "You":
        return False
    fingerprint = row.get("fingerprint")
    if after_fingerprint and (not fingerprint or str(fingerprint) <= after_fingerprint):
        return False
    if sender in _MIND_SENDERS:
        return True
    if row.get("mindId"):
        return True
    sender_name = row.get("senderName")
    if isinstance(sender_name, str) and sender_name and sender_name != "You":
        return True
    return False


def extract_json_payload(text: str) -> Any:
    """Parse an asset list from a Mind reply. Ignore prose brackets like [HOOK]."""
    stripped = (text or "").strip()
    blobs: list[str] = []
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL | re.IGNORECASE)
    if fenced:
        blobs.append(fenced.group(1).strip())
    blobs.append(stripped)
    decoder = json.JSONDecoder()
    last_error: Exception | None = None
    for blob in blobs:
        for match in re.finditer(r"[\{\[]", blob):
            snippet = blob[match.start() :]
            if snippet.startswith("[") and not re.match(r"\[\s*(\{|\[)", snippet):
                continue
            try:
                obj, _end = decoder.raw_decode(snippet)
            except json.JSONDecodeError as exc:
                last_error = exc
                continue
            if _looks_like_asset_payload(obj):
                if isinstance(obj, dict) and "assets" not in obj and obj.get("type"):
                    return [obj]
                return obj
    raise ValueError("Mind reply did not contain a JSON asset list") from last_error


def _looks_like_asset_payload(obj: Any) -> bool:
    if isinstance(obj, list):
        dicts = [item for item in obj if isinstance(item, dict)]
        return any(
            str(item.get("type") or item.get("content") or item.get("text") or "").strip()
            for item in dicts
        )
    if isinstance(obj, dict):
        if isinstance(obj.get("assets"), list):
            return _looks_like_asset_payload(obj["assets"])
        return bool(obj.get("type") and (obj.get("content") or obj.get("text")))
    return False


def parse_asset_list(payload: Any) -> list[dict[str, Any]]:
    assets = payload
    if isinstance(payload, dict):
        assets = payload.get("assets", payload)
    if not isinstance(assets, list) or not assets:
        raise ValueError("Minds generate response did not include an assets list")
    parsed: list[dict[str, Any]] = []
    for item in assets:
        if not isinstance(item, dict):
            continue
        asset_type = str(item.get("type") or "").strip()
        content = item.get("content") or item.get("text") or ""
        if not asset_type or not str(content).strip():
            continue
        parsed.append(
            {
                "type": asset_type,
                "platform": item.get("platform") or "kdp",
                "content": str(content).strip(),
                "source_references": item.get("source_references") or [],
                "assumptions": item.get("assumptions") or [],
                "call_to_action": item.get("call_to_action") or "",
                "risk_notes": item.get("risk_notes") or [],
                "approval_status": item.get("approval_status") or "draft",
            }
        )
    if not parsed:
        raise ValueError("Minds generate response did not include usable assets")
    return parsed


class MindsClient:
    """Server-side adapter for the Minds Builder API.

    Contract matches @animocabrands/minds-client-lib (v0.1.3):
    X-Api-Key, conversation alias, POST /v1/messaging/message, wait on history.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        alias: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        raw_url = base_url if base_url is not None else settings.MINDS_API_BASE_URL
        self.base_url = normalize_base_url(raw_url)
        key = api_key if api_key is not None else settings.MINDS_API_KEY
        self.api_key = key.get_secret_value() if key is not None and hasattr(key, "get_secret_value") else key
        if isinstance(self.api_key, str) and not self.api_key.strip():
            self.api_key = None
        self.alias = alias or settings.MINDS_CONVERSATION_ALIAS or DEFAULT_ALIAS
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def require_configured(self) -> None:
        if not self.configured:
            raise MindsNotConfigured(
                "Minds is not configured. Set MINDS_API_KEY on the API."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "X-Api-Key": str(self.api_key),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _client(self, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            transport=self._transport,
        )

    async def _request(
        self,
        http: httpx.AsyncClient,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_409: bool = False,
        retry_502: bool = False,
    ) -> Any:
        url = f"{self.base_url}{path}"
        last_error: MindsApiError | None = None
        attempts = 3 if (retry_409 or retry_502) else 1
        delays = (0.2, 0.4, 0.8)
        for attempt in range(attempts):
            response = await http.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
                params=params,
            )
            if response.is_success:
                if response.status_code == 204 or not response.content:
                    return None
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return response.text
            detail = response.text[:500]
            try:
                body = response.json()
                if isinstance(body, dict):
                    error = body.get("error")
                    if isinstance(error, dict):
                        detail = str(error.get("message") or detail)
                    elif isinstance(error, str):
                        detail = error
                    elif body.get("message"):
                        detail = str(body["message"])
            except json.JSONDecodeError:
                pass
            last_error = MindsApiError(
                f"Minds API {method} {path} failed ({response.status_code}): {detail}",
                status=response.status_code,
            )
            retry = (retry_409 and response.status_code == 409) or (
                retry_502 and response.status_code == 502
            )
            if not retry or attempt == attempts - 1:
                break
            await asyncio.sleep(delays[min(attempt, len(delays) - 1)])
        assert last_error is not None
        raise last_error

    async def ensure_conversation(self, http: httpx.AsyncClient, mind_id: str, alias: str) -> dict[str, Any]:
        try:
            data = await self._request(
                http,
                "POST",
                "/v1/messaging/conversation",
                json_body={"alias": alias, "mindId": mind_id},
            )
            return data if isinstance(data, dict) else {"alias": alias, "mindId": mind_id}
        except MindsApiError as exc:
            if exc.status not in {400, 409}:
                raise
            existing = await self._request(
                http,
                "GET",
                f"/v1/messaging/conversations/{alias}",
                retry_502=True,
            )
            row = existing if isinstance(existing, dict) else {}
            existing_mind = row.get("mindId")
            if isinstance(existing_mind, str) and existing_mind and existing_mind != mind_id:
                raise MindsApiError(
                    f'Alias "{alias}" is bound to a different Mind.',
                    status=409,
                    code="alias_mind_mismatch",
                ) from exc
            return row

    async def _latest_fingerprint(self, http: httpx.AsyncClient, alias: str) -> str | None:
        try:
            data = await self._request(
                http,
                "GET",
                f"/v1/messaging/histories/{alias}",
                params={"limit": 50},
                retry_502=True,
            )
        except MindsApiError:
            return None
        rows = _as_rows(data)
        if not rows:
            return None
        fingerprint = rows[-1].get("fingerprint")
        return str(fingerprint) if fingerprint else None

    async def _wait_for_reply(
        self,
        http: httpx.AsyncClient,
        *,
        alias: str,
        sent_text: str,
        after_fingerprint: str | None,
        timeout_s: float,
    ) -> str:
        end = time.monotonic() + float(timeout_s)
        while True:
            data = await self._request(
                http,
                "GET",
                f"/v1/messaging/histories/{alias}",
                params={
                    "limit": 50,
                    **({"after": after_fingerprint} if after_fingerprint else {}),
                },
                retry_502=True,
            )
            for row in _as_rows(data):
                if _is_mind_reply(
                    row,
                    sent_text=sent_text,
                    after_fingerprint=after_fingerprint,
                    alias=alias,
                ):
                    return _message_text(row)
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise MindsApiError(
                    "Timed out waiting for a Mind reply.",
                    status=504,
                    code="timeout",
                )
            await asyncio.sleep(min(2.0, remaining))

    async def message(
        self,
        mind_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        *,
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        """Send a chat turn and wait for the Mind reply."""
        self.require_configured()
        del metadata  # Builder send body is alias + messageText only.
        alias = self.alias
        wait_s = float(timeout_s or settings.MINDS_REPLY_TIMEOUT_SECONDS)
        async with self._client(wait_s + 15) as http:
            await self.ensure_conversation(http, mind_id, alias)
            after = await self._latest_fingerprint(http, alias)
            await self._request(
                http,
                "POST",
                "/v1/messaging/message",
                json_body={"alias": alias, "messageText": text},
                retry_409=True,
            )
            reply = await self._wait_for_reply(
                http,
                alias=alias,
                sent_text=text,
                after_fingerprint=after,
                timeout_s=wait_s,
            )
        return {"reply": reply, "raw": {"alias": alias, "mindId": mind_id}}

    async def generate_assets(
        self,
        mind_id: str,
        request: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Ask the Mind in chat for a JSON asset list. There is no generate endpoint."""
        result = await self.message(
            mind_id,
            _assets_prompt(request),
            timeout_s=max(settings.MINDS_REPLY_TIMEOUT_SECONDS, 180),
        )
        try:
            payload = extract_json_payload(result["reply"])
            return parse_asset_list(payload)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Mind did not return a JSON asset list"
            ) from exc


def _assets_prompt(request: dict[str, Any]) -> str:
    book = request.get("book") or {}
    author = request.get("author") or {}
    types = request.get("asset_types") or [
        "description",
        "newsletter",
        "social_post",
        "podcast_pitch",
        "video_script",
    ]
    correction = request.get("correction")
    correction_block = (
        f"\nAuthor correction to apply: {correction}\n" if correction else ""
    )
    return (
        "You are this author's publishing Mind. Return ONLY a JSON array of assets. "
        "No markdown, no preamble.\n"
        "Each object must have: type, platform, content, source_references "
        "(array of {kind, quote, note}), assumptions (string array), "
        "call_to_action (string), risk_notes (string array).\n"
        f"Required types in order: {', '.join(types)}.\n"
        "Do not invent guaranteed sales, medical advice, or legal clearance. "
        "Quote the excerpt in source_references.\n"
        f"Book title: {book.get('title')}\n"
        f"Subtitle: {book.get('subtitle')}\n"
        f"Author: {author.get('name')}\n"
        f"Voice: {author.get('voice')}\n"
        f"Audience: {author.get('audience')}\n"
        f"{correction_block}"
        "Excerpt:\n"
        f"{request.get('excerpt') or ''}\n"
    )
