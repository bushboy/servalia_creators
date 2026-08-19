from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from thebe_core.models import (
    EntityContext,
    EvaluationResult,
    RulePack,
    RuleResult,
    Violation,
)

UNKNOWN = object()


class UnknownFieldError(Exception):
    """Raised when a DSL path cannot be resolved or is explicitly "not_sure"."""


class PolicyEngine:
    """Evaluates an in-memory projection against a vertical RulePack."""

    def __init__(self, predicates: dict[str, Callable[[EntityContext], bool]] | None = None):
        self.predicates = dict(predicates or {})

    def register_predicate(self, name: str, predicate: Callable[[EntityContext], bool]) -> None:
        """Register a named predicate callable."""
        self.predicates[name] = predicate

    def evaluate(self, context: EntityContext, rule_pack: RulePack) -> EvaluationResult:
        """Run every control rule and return a five-state EvaluationResult."""
        rule_results: list[RuleResult] = []
        required_actions: list[str] = []

        controls = context.attributes.get("controls", {})
        evidence = context.attributes.get("evidence", {})

        for rule in rule_pack.rules:
            result = self._evaluate_control_rule(rule, context, controls, evidence)
            rule_results.append(result)
            if result.status in {"FAIL", "PARTIAL"}:
                required_actions.extend(rule.recommended_actions or [])

        violations = [
            Violation(
                rule_id=r.rule_id,
                control_key=r.control_key,
                obligation_key=r.obligation_key,
                description=r.description,
                severity=r.severity,
                recommended_actions=r.recommended_actions,
                source_fields=r.source_fields,
                evidence_ids=r.evidence_ids,
            )
            for r in rule_results
            if r.status in {"FAIL", "PARTIAL"}
        ]

        assessed = [r for r in rule_results if r.status in {"PASS", "PARTIAL", "FAIL"}]
        if assessed:
            n_pass = sum(1 for r in assessed if r.status == "PASS")
            n_partial = sum(1 for r in assessed if r.status == "PARTIAL")
            score = round((n_pass + 0.5 * n_partial) / len(assessed), 4)
        else:
            score = None

        return EvaluationResult(
            vertical=rule_pack.vertical,
            entity_type=context.entity_type,
            score=score,
            rule_results=rule_results,
            violations=violations,
            required_actions=list(dict.fromkeys(required_actions)),
        )

    def _evaluate_control_rule(
        self,
        rule: Any,
        context: EntityContext,
        controls: dict[str, Any],
        evidence: dict[str, list[dict[str, Any]]],
    ) -> RuleResult:
        applies_when = rule.applies_when
        applies = self._evaluate_condition(applies_when, context) if applies_when is not None else True

        source_fields = self._collect_paths(applies_when) + self._collect_paths(rule.check)

        if applies is UNKNOWN:
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="UNKNOWN",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=source_fields,
            )

        if not applies:
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="NOT_APPLICABLE",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=source_fields,
            )

        # Phase 2 checklist semantics: if we have a recorded answer, it drives the status.
        answer = self._get_control_answer(rule.control_key, controls)
        if answer is not None:
            source_fields.append(self._control_answer_path(rule.control_key))
            if answer in ("unanswered", "not_sure"):
                return RuleResult(
                    rule_id=rule.rule_id,
                    control_key=rule.control_key,
                    obligation_key=rule.obligation_key,
                    status="UNKNOWN",
                    severity=rule.severity,
                    description=rule.description,
                    recommended_actions=rule.recommended_actions,
                    source_fields=sorted(set(source_fields)),
                )
            if answer == "no":
                return RuleResult(
                    rule_id=rule.rule_id,
                    control_key=rule.control_key,
                    obligation_key=rule.obligation_key,
                    status="FAIL",
                    severity=rule.severity,
                    description=rule.description,
                    recommended_actions=rule.recommended_actions,
                    source_fields=sorted(set(source_fields)),
                )
            # answer == "yes" (or equivalent)
            evidence_ids = self._active_evidence_ids(rule.control_key, evidence)
            if rule.evidence_required and not evidence_ids:
                return RuleResult(
                    rule_id=rule.rule_id,
                    control_key=rule.control_key,
                    obligation_key=rule.obligation_key,
                    status="PARTIAL",
                    severity=rule.severity,
                    description=rule.description,
                    recommended_actions=rule.recommended_actions,
                    source_fields=sorted(set(source_fields)),
                    evidence_ids=[],
                )
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="PASS",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=sorted(set(source_fields)),
                evidence_ids=evidence_ids,
            )

        # No stored answer yet: fall back to the legacy/declarative check condition.
        try:
            check_true = self._evaluate_condition(rule.check, context)
        except UnknownFieldError:
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="UNKNOWN",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=source_fields,
            )

        if check_true is UNKNOWN:
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="UNKNOWN",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=source_fields,
            )

        if not check_true:
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="FAIL",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=source_fields,
            )

        evidence_ids = self._active_evidence_ids(rule.control_key, evidence)
        if rule.evidence_required and not evidence_ids:
            return RuleResult(
                rule_id=rule.rule_id,
                control_key=rule.control_key,
                obligation_key=rule.obligation_key,
                status="PARTIAL",
                severity=rule.severity,
                description=rule.description,
                recommended_actions=rule.recommended_actions,
                source_fields=source_fields,
                evidence_ids=[],
            )

        return RuleResult(
            rule_id=rule.rule_id,
            control_key=rule.control_key,
            obligation_key=rule.obligation_key,
            status="PASS",
            severity=rule.severity,
            description=rule.description,
            recommended_actions=rule.recommended_actions,
            source_fields=source_fields,
            evidence_ids=evidence_ids,
        )

    def _evaluate_condition(
        self,
        condition: Callable[[EntityContext], bool] | dict[str, Any] | str | None,
        context: EntityContext,
    ) -> Any:
        if condition is None:
            return False

        if callable(condition):
            return bool(condition(context))

        if isinstance(condition, str):
            if condition in self.predicates:
                return bool(self.predicates[condition](context))
            raise ValueError(f"Unknown named predicate or DSL string: {condition!r}")

        if isinstance(condition, dict):
            return self._evaluate_dsl(condition, context)

        raise ValueError(f"Unsupported condition type: {type(condition)}")

    def _evaluate_dsl(self, node: dict[str, Any], context: EntityContext) -> Any:
        op = node.get("op")

        if op == "exists":
            value, _ = self._resolve(node["path"], context)
            return value is not None and value != ""
        if op == "not_exists":
            value, _ = self._resolve(node["path"], context)
            return value is None or value == ""

        if op == "not":
            child = self._evaluate_dsl(node["condition"], context)
            if child is UNKNOWN:
                return UNKNOWN
            return not child

        if op == "and":
            has_unknown = False
            for child in node.get("conditions", []):
                val = self._evaluate_condition(child, context)
                if val is UNKNOWN:
                    has_unknown = True
                    continue
                if not val:
                    return False
            return UNKNOWN if has_unknown else True

        if op == "or":
            has_unknown = False
            for child in node.get("conditions", []):
                val = self._evaluate_condition(child, context)
                if val is UNKNOWN:
                    has_unknown = True
                    continue
                if val:
                    return True
            return UNKNOWN if has_unknown else False

        left, missing = self._resolve(node["path"], context)

        if missing or left == "not_sure":
            return UNKNOWN

        if op in {"eq", "equals"}:
            return left == node["value"]
        if op in {"ne", "neq", "not_equals"}:
            return left != node["value"]
        if op == "gt":
            return left > node["value"]
        if op == "gte":
            return left >= node["value"]
        if op == "lt":
            return left < node["value"]
        if op == "lte":
            return left <= node["value"]
        if op == "in":
            return left in node["value"]
        if op == "contains":
            return node["value"] in left

        raise ValueError(f"Unknown DSL operator: {op!r}")

    def _resolve(self, path: str, context: EntityContext) -> tuple[Any, bool]:
        if path.startswith("attributes."):
            path = path[len("attributes.") :]

        parts = path.split(".")
        value = context.attributes
        missing = False
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                missing = True
                break
            value = value[part]
        if missing:
            return None, True
        return value, False

    def _collect_paths(self, node: Any, paths: list[str] | None = None) -> list[str]:
        if paths is None:
            paths = []
        if isinstance(node, dict):
            if "path" in node and isinstance(node["path"], str):
                paths.append(node["path"])
            for value in node.values():
                self._collect_paths(value, paths)
        elif isinstance(node, list):
            for item in node:
                self._collect_paths(item, paths)
        return sorted(set(paths))

    def _get_control_answer(
        self,
        control_key: str | None,
        controls: dict[str, Any],
    ) -> str | None:
        if not control_key:
            return None
        entry = controls.get(control_key, {})
        if isinstance(entry, dict):
            return entry.get("answer")
        return None

    def _control_answer_path(self, control_key: str | None) -> str:
        return f"controls.{control_key}.answer" if control_key else ""

    def _active_evidence_ids(
        self,
        control_key: str | None,
        evidence: dict[str, list[dict[str, Any]]],
    ) -> list[str]:
        if not control_key:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        ids: list[str] = []
        for item in evidence.get(control_key, []):
            ts = item.get("updated_at") or item.get("created_at")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if ts is None or ts >= cutoff:
                ids.append(str(item["evidence_id"]))
        return ids
