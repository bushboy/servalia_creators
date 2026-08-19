from __future__ import annotations

from thebe_core.models import EntityContext, Rule, RulePack
from thebe_core.policy.engine import PolicyEngine
from thebe_core.policy.loader import RuleLoader


def test_load_json_rule_pack():
    raw = """
{
    "vertical": "test",
    "rules": [
        {
            "rule_id": "JSON-001",
            "description": "JSON test rule.",
            "severity": "low",
            "condition": {"op": "exists", "path": "context.demo"},
            "recommended_actions": ["Action A"]
        }
    ]
}
"""
    pack = RuleLoader.loads(raw, format=".json")
    assert pack.vertical == "test"
    assert pack.rules[0].rule_id == "JSON-001"


def test_named_predicate():
    engine = PolicyEngine()
    engine.register_predicate(
        "is_crypto",
        lambda ctx: ctx.attributes.get("context", {}).get("product") == "crypto",
    )
    rule = Rule(
        rule_id="NP-001",
        description="Named predicate test.",
        severity="medium",
        check="is_crypto",
        recommended_actions=["Check predicate."],
    )
    pack = RulePack(vertical="test", rules=[rule])
    context = EntityContext(
        entity_type="asset", attributes={"context": {"product": "lending"}}
    )
    result = engine.evaluate(context, pack)
    assert len(result.violations) == 1
    assert result.violations[0].rule_id == "NP-001"


def test_callable_condition():
    engine = PolicyEngine()
    rule = Rule(
        rule_id="CALL-001",
        description="Callable condition test.",
        severity="low",
        check=lambda ctx: ctx.attributes.get("context", {}).get("count", 0) > 5,
        recommended_actions=["Reduce count."],
    )
    pack = RulePack(vertical="test", rules=[rule])
    context = EntityContext(entity_type="asset", attributes={"context": {"count": 2}})
    result = engine.evaluate(context, pack)
    assert len(result.violations) == 1
