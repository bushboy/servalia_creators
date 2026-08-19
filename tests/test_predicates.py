from __future__ import annotations

from thebe_core.creator.predicates import creator_predicates
from thebe_core.models import EntityContext, Rule, RulePack
from thebe_core.policy.engine import PolicyEngine


GUARANTEE = "This method guarantees that every new author will double their book sales."


def _context(text: str, **author: object) -> EntityContext:
    return EntityContext(
        entity_type="asset",
        attributes={
            "author": {
                "rights": "all_rights_owned",
                "display_name": "Mara Ellison",
                "publisher_name": "Ellison Press",
                "preferred_terms": "reader",
                **author,
            },
            "author_name": "Mara Ellison",
            "asset": {"content": text, "type": "description"},
            "text": text,
            "edition": {
                "format": "paperback",
                "isbn": "9781234567897",
                "platform_strategy": {"publisher_field": "Mara Ellison"},
            },
        },
    )


def test_guarantee_sentence_fails_claim_predicate():
    predicates = creator_predicates()
    assert predicates["no_unsupported_guarantee"](_context("A calm excerpt about voice."))
    assert not predicates["no_unsupported_guarantee"](_context(GUARANTEE))


def test_claim_rule_is_fail_before_review_mapping():
    engine = PolicyEngine(predicates=creator_predicates())
    pack = RulePack(
        vertical="creator_publishing",
        rules=[
            Rule(
                rule_id="CREATOR-CLAIM-001",
                description="Unsupported guarantee",
                check="no_unsupported_guarantee",
                recommended_actions=["Rewrite the claim."],
            )
        ],
    )
    result = engine.evaluate(_context(GUARANTEE), pack)
    assert result.rule_results[0].status == "FAIL"
    assert result.rule_results[0].rule_id == "CREATOR-CLAIM-001"
