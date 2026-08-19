from __future__ import annotations

import json

import httpx
import pytest

from thebe_core.minds.client import (
    MindsClient,
    MindsNotConfigured,
    extract_json_payload,
    format_mind_reply,
    normalize_base_url,
    parse_asset_list,
)


def test_normalize_base_url_strips_v1_suffix():
    assert normalize_base_url("https://api.build.hellominds.ai/v1/") == (
        "https://api.build.hellominds.ai"
    )
    assert normalize_base_url("https://api.build.hellominds.ai") == (
        "https://api.build.hellominds.ai"
    )
    assert normalize_base_url(None) == "https://api.build.hellominds.ai"


def test_format_mind_reply_converts_html():
    html = (
        "<div><p>Keep the voice <strong>warm</strong>.</p>"
        "<p>Avoid guaranteed sales.</p><ul><li>Rights first</li>"
        "<li>Author approves</li></ul></div>"
    )
    text = format_mind_reply(html)
    assert "<p>" not in text
    assert "Keep the voice warm." in text
    assert "Avoid guaranteed sales." in text
    assert "• Rights first" in text
    assert "• Author approves" in text


def test_format_mind_reply_leaves_plain_text():
    assert format_mind_reply("Keep the voice warm.") == "Keep the voice warm."


def test_extract_json_ignores_script_brackets():
    with pytest.raises(ValueError, match="JSON asset list"):
        extract_json_payload(
            "[HOOK] Manuscript to Launch does not promise guaranteed sales.\n"
            "[STORY] Start where the manuscript is.\n"
            "[CTA] Follow for the launch plan."
        )


def test_extract_json_from_prose_then_array():
    payload = extract_json_payload(
        'Sure — here is the pack:\n[{"type": "description", "content": "A governed launch."}]'
    )
    assets = parse_asset_list(payload)
    assert assets[0]["content"] == "A governed launch."


def test_extract_json_from_fenced_reply():
    payload = extract_json_payload(
        'Here you go:\n```json\n{"assets": [{"type": "description", "content": "x"}]}\n```'
    )
    assets = parse_asset_list(payload)
    assert assets[0]["type"] == "description"


class FakeBuilder:
    def __init__(self) -> None:
        self.paths: list[tuple[str, str]] = []
        self.history_gets = 0
        self.last_headers: dict[str, str] = {}
        self.last_message_body: dict | None = None
        self.create_status = 200

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.paths.append((request.method, request.url.path))
        self.last_headers = {k.lower(): v for k, v in request.headers.items()}
        path = request.url.path
        if request.method == "POST" and path == "/v1/messaging/conversation":
            if self.create_status != 200:
                return httpx.Response(self.create_status, json={"message": "exists"})
            return httpx.Response(
                200, json={"alias": "creatortrust", "mindId": "mind-1"}
            )
        if request.method == "GET" and path == "/v1/messaging/conversations/creatortrust":
            return httpx.Response(
                200, json={"alias": "creatortrust", "mindId": "mind-1"}
            )
        if request.method == "GET" and path == "/v1/messaging/histories/creatortrust":
            self.history_gets += 1
            if self.history_gets == 1:
                return httpx.Response(
                    200,
                    json=[
                        {
                            "fingerprint": "a",
                            "messageText": "prior",
                            "senderType": 1,
                        }
                    ],
                )
            return httpx.Response(
                200,
                json=[
                    {
                        "fingerprint": "a",
                        "messageText": "prior",
                        "senderType": 1,
                    },
                    {
                        "fingerprint": "b",
                        "messageText": (
                            "<p>Keep the voice <strong>warm</strong> and skip "
                            "guaranteed sales.</p>"
                        ),
                        "senderType": 0,
                        "mindId": "mind-1",
                    },
                ],
            )
        if request.method == "POST" and path == "/v1/messaging/message":
            self.last_message_body = json.loads(request.content.decode())
            return httpx.Response(200, json={"alias": "creatortrust"})
        return httpx.Response(404, json={"message": f"unhandled {path}"})


@pytest.mark.asyncio
async def test_message_uses_builder_contract():
    fake = FakeBuilder()
    client = MindsClient(
        base_url="https://api.build.hellominds.ai/v1/",
        api_key="test-key",
        transport=httpx.MockTransport(fake),
    )
    result = await client.message("mind-1", "What should we avoid?", timeout_s=5)
    assert result["reply"] == "Keep the voice warm and skip guaranteed sales."
    assert fake.last_headers.get("x-api-key") == "test-key"
    assert "authorization" not in fake.last_headers
    assert fake.last_message_body == {
        "alias": "creatortrust",
        "messageText": "What should we avoid?",
    }
    assert ("POST", "/v1/messaging/conversation") in fake.paths
    assert ("POST", "/v1/messaging/message") in fake.paths
    assert ("GET", "/v1/messaging/histories/creatortrust") in fake.paths
    assert all("/v1/minds/" not in path for _, path in fake.paths)


@pytest.mark.asyncio
async def test_ensure_conversation_reuses_existing_alias():
    fake = FakeBuilder()
    fake.create_status = 409
    client = MindsClient(
        base_url="https://api.build.hellominds.ai",
        api_key="test-key",
        transport=httpx.MockTransport(fake),
    )
    result = await client.message("mind-1", "Hello", timeout_s=5)
    assert "warm" in result["reply"]
    assert ("GET", "/v1/messaging/conversations/creatortrust") in fake.paths


@pytest.mark.asyncio
async def test_generate_assets_parses_chat_json():
    fake = FakeBuilder()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/histories/creatortrust"):
            fake.history_gets += 1
            if fake.history_gets == 1:
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[
                    {
                        "fingerprint": "z",
                        "senderType": 0,
                        "messageText": json.dumps(
                            [
                                {
                                    "type": "description",
                                    "platform": "kdp",
                                    "content": "A governed launch.",
                                    "source_references": [],
                                    "assumptions": [],
                                    "call_to_action": "Approve",
                                    "risk_notes": [],
                                }
                            ]
                        ),
                    }
                ],
            )
        return fake(request)

    client = MindsClient(
        base_url="https://api.build.hellominds.ai",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )
    assets = await client.generate_assets(
        "mind-1",
        {
            "book": {"title": "Manuscript to Launch"},
            "author": {"name": "Mara"},
            "excerpt": "Start where the manuscript is.",
            "asset_types": ["description"],
        },
    )
    assert assets[0]["type"] == "description"
    assert "governed" in assets[0]["content"]


def test_unconfigured_client_raises():
    client = MindsClient(base_url="https://api.build.hellominds.ai", api_key="")
    with pytest.raises(MindsNotConfigured):
        client.require_configured()
