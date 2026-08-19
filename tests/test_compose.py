from __future__ import annotations

from thebe_core.creator.compose import REVISED_CLAIM, RISKY_CLAIM, compose_assets
from thebe_core.creator.seed import SEED_CONTEXT, _excerpt_text


def test_seed_excerpt_is_demo_length_and_keeps_the_claim():
    text = _excerpt_text()
    words = text.split()
    assert 400 <= len(words) <= 700
    assert RISKY_CLAIM in text
    assert "Chapter 1 — Start where the manuscript is" in text


def test_seed_context_uses_existing_string_fields():
    assert SEED_CONTEXT["voice"].startswith("Practical")
    assert "First-time authors" in SEED_CONTEXT["audience"]
    assert "publishing workflow" in SEED_CONTEXT["preferred_terms"]
    assert "guaranteed sales" in SEED_CONTEXT["prohibited_topics"]
    assert "medical advice" not in SEED_CONTEXT["prohibited_topics"]


def test_description_carries_the_claim_other_channels_do_not():
    excerpt = _excerpt_text()
    assets = {
        row["type"]: row
        for row in compose_assets(
            title="Manuscript to Launch",
            excerpt=excerpt,
            author_name="Mara Ellison",
            voice=SEED_CONTEXT["voice"],
            audience=SEED_CONTEXT["audience"],
            preferred_terms=SEED_CONTEXT["preferred_terms"],
            rights=SEED_CONTEXT["rights"],
        )
    }
    assert set(assets) == {
        "description",
        "newsletter",
        "social_post",
        "podcast_pitch",
        "video_script",
    }
    assert RISKY_CLAIM in assets["description"]["content"]
    assert RISKY_CLAIM not in assets["newsletter"]["content"]
    assert RISKY_CLAIM not in assets["social_post"]["content"]
    assert "guaranteed sales" not in assets["video_script"]["content"].lower()
    assert assets["description"]["source_references"][0]["quote"] == RISKY_CLAIM
    assert "all_rights_owned" in " ".join(assets["description"]["assumptions"])


def test_revise_replaces_the_claim_and_keeps_useful_copy():
    excerpt = _excerpt_text()
    revised = compose_assets(
        title="Manuscript to Launch",
        excerpt=excerpt,
        author_name="Mara Ellison",
        voice=SEED_CONTEXT["voice"],
        audience=SEED_CONTEXT["audience"],
        preferred_terms=SEED_CONTEXT["preferred_terms"],
        correction="Do not use guaranteed results or aggressive sales language.",
        asset_types=["description"],
        rights="all_rights_owned",
    )[0]
    assert "Applied author preference" in revised["content"]
    assert RISKY_CLAIM not in revised["content"]
    assert REVISED_CLAIM in revised["content"]
    assert "guaranteed" not in revised["content"].lower()
