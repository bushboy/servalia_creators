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

RISKY_CLAIM = (
    "This method guarantees that every new author will double their book sales."
)
REVISED_CLAIM = (
    "This method gives first-time authors a practical workflow for preparing a coordinated launch."
)


def _quote(excerpt: str, max_chars: int = 280) -> str:
    text = " ".join(excerpt.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rsplit(" ", 1)[0] + "…"


def _claim_line(excerpt: str, correction: str | None) -> str | None:
    if RISKY_CLAIM not in excerpt:
        return None
    if correction:
        lowered = correction.lower()
        if "guarantee" in lowered or "aggressive" in lowered:
            return REVISED_CLAIM
    return RISKY_CLAIM


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
    rights: str | None = None,
) -> list[dict[str, Any]]:
    """Deterministic structured assets when the Minds API is not configured.

    Used for tests and local loops. Chat still requires a real Mind.
    The book description carries the seeded commercial claim so governance
    review stays visible; other channels reuse the opening manuscript lines.
    """
    quote = _quote(excerpt)
    claim = _claim_line(excerpt, correction)
    terms = preferred_terms or "manuscript, reader, publishing workflow"
    rights_status = rights or "unknown"
    preference_note = ""
    if correction:
        preference_note = "Applied author preference.\n\n"

    claim_sentence = f" {claim}" if claim else ""
    description_body = (
        f"{title} by {author_name} is a practical publishing workflow for "
        f"{audience or 'first-time authors'}. "
        f"Written in a {voice or 'practical'} voice, it treats the manuscript as the "
        f"source material and keeps author approval in view.{claim_sentence} "
        f"Start with the reader. Adapt the message for each channel. "
        f"Review every public-facing claim before a submission package is prepared."
    )
    templates = {
        "description": f"{preference_note}{description_body}",
        "newsletter": (
            f"Subject: {title} is ready for your publishing workflow\n\n"
            f"Hello,\n\n{preference_note}"
            f"I wrote {title} for {audience or 'readers'} who have a finished "
            f"manuscript and still need a coordinated launch. "
            f"Here is a line from the source material:\n\n“{quote}”\n\n"
            f"If you are preparing author approval for public copy, reply and tell me "
            f"where you are in the process."
        ),
        "social_post": (
            f"{preference_note}"
            f"{title} — a note for the first-time author.\n\n“{quote}”\n\n"
            f"Voice: {voice or 'practical'}. Built from the manuscript for the reader, "
            f"not a marketplace algorithm."
        ),
        "podcast_pitch": (
            f"Pitch: {author_name} on turning one manuscript into a publishing workflow.\n\n"
            f"{preference_note}"
            f"Suggested topic: how {audience or 'authors'} keep voice, rights, and "
            f"author approval while preparing KDP and IngramSpark. "
            f"Excerpt: “{quote}”"
        ),
        "video_script": (
            f"{preference_note}"
            f"[HOOK] {title} starts where the manuscript is.\n"
            f"[STORY] {quote}\n"
            f"[CTA] Follow for a practical publishing workflow. {terms}."
        ),
    }

    wanted = set(asset_types) if asset_types else {spec["type"] for spec in ASSET_SPECS}
    assets: list[dict[str, Any]] = []
    for spec in ASSET_SPECS:
        if spec["type"] not in wanted:
            continue
        source_quote = claim if spec["type"] == "description" and claim else quote
        assets.append(
            {
                "type": spec["type"],
                "platform": spec["platform"],
                "content": templates[spec["type"]].strip(),
                "source_references": [
                    {
                        "kind": "excerpt",
                        "quote": source_quote,
                        "note": f"Drawn from the uploaded manuscript for the {spec['label']}.",
                    }
                ],
                "assumptions": [
                    f"Audience is {audience or 'the stated reader'}.",
                    f"Voice is {voice or 'the author’s declared voice'}.",
                    f"Rights declared as {rights_status}.",
                    "Source material is the uploaded manuscript excerpt.",
                ],
                "call_to_action": "Approve this asset before it is packaged.",
                "risk_notes": [
                    "Creator-configured governance review is required before packaging."
                ],
                "approval_status": "draft",
            }
        )
    return assets
