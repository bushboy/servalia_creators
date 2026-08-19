from __future__ import annotations

from typing import Any

ASSET_SPECS: list[dict[str, str]] = [
    {
        "type": "description",
        "platform": "kdp",
        "label": "book description",
    },
    {
        "type": "newsletter",
        "platform": "email",
        "label": "launch newsletter",
    },
    {
        "type": "social_post",
        "platform": "social",
        "label": "social post",
    },
    {
        "type": "podcast_pitch",
        "platform": "podcast",
        "label": "podcast pitch",
    },
    {
        "type": "video_script",
        "platform": "video",
        "label": "short-form video script",
    },
]


def _quote(excerpt: str, max_chars: int = 280) -> str:
    text = " ".join(excerpt.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def compose_assets(
    *,
    title: str,
    excerpt: str,
    author_name: str,
    voice: str,
    audience: str,
    preferred_terms: str,
    correction: str | None = None,
    asset_types: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Deterministic structured assets when the Minds API is not configured.

    Used for tests and local loops. Chat still requires a real Mind.
    """
    quote = _quote(excerpt)
    terms = preferred_terms or "reader"
    preference_note = ""
    body_excerpt = excerpt
    if correction:
        preference_note = f"Applied author preference: {correction.strip()}\n\n"
        lowered = correction.lower()
        if "guarantee" in lowered or "aggressive" in lowered:
            body_excerpt = excerpt.replace(
                "This method guarantees that every new author will double their book sales.",
                "This method helps a reader move from manuscript to a coordinated launch.",
            )

    templates = {
        "description": (
            f"{title} by {author_name}. Written in a {voice or 'clear'} voice for {audience or 'readers'}. "
            f"{body_excerpt.strip()}\n\n"
            f"For the independent author and every reader who wants a governed publishing path."
        ),
        "newsletter": (
            f"Subject: {title} is ready for readers\n\n"
            f"Hello,\n\n{preference_note}"
            f"I wrote {title} for {audience or 'readers'} who are stuck between a finished draft and a launch. "
            f"Here is a line from the manuscript:\n\n“{quote}”\n\n"
            f"If you are an independent author, reply and tell me where you are in the process."
        ),
        "social_post": (
            f"{preference_note}"
            f"{title} — a note for the independent author.\n\n“{quote}”\n\n"
            f"Voice: {voice or 'practical'}. Built for the reader, not a marketplace algorithm."
        ),
        "podcast_pitch": (
            f"Pitch: {author_name} on turning one manuscript into a governed launch.\n\n"
            f"{preference_note}"
            f"Suggested topic: how {audience or 'authors'} keep voice and rights while preparing KDP and IngramSpark. "
            f"Excerpt: “{quote}”"
        ),
        "video_script": (
            f"[HOOK] {title} does not promise guaranteed sales. It gives the reader a path.\n"
            f"[STORY] {quote}\n"
            f"[CTA] Follow for the launch plan. {terms}."
        ),
    }

    wanted = set(asset_types) if asset_types else {spec["type"] for spec in ASSET_SPECS}
    assets: list[dict[str, Any]] = []
    for spec in ASSET_SPECS:
        if spec["type"] not in wanted:
            continue
        content = preference_note + templates[spec["type"]] if spec["type"] not in {
            "newsletter",
            "social_post",
            "podcast_pitch",
        } else templates[spec["type"]]
        assets.append(
            {
                "type": spec["type"],
                "platform": spec["platform"],
                "content": content.strip(),
                "source_references": [
                    {
                        "kind": "excerpt",
                        "quote": quote,
                        "note": f"Drawn from the uploaded manuscript for the {spec['label']}.",
                    }
                ],
                "assumptions": [
                    f"Audience is {audience or 'the stated reader'}.",
                    f"Voice is {voice or 'the author’s declared voice'}.",
                ],
                "call_to_action": "Approve this asset before it is packaged.",
                "risk_notes": [
                    "Creator-configured governance review is required before packaging."
                ],
                "approval_status": "draft",
            }
        )
    return assets
