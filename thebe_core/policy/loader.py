from __future__ import annotations

import json
import pathlib
from typing import Any

import yaml

from thebe_core.models import RulePack


class RuleLoader:
    """Load a RulePack from a YAML or JSON rule file."""

    @staticmethod
    def load(path: str | pathlib.Path) -> RulePack:
        """Load a RulePack from a file."""
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Rule file not found: {path}")

        text = path.read_text(encoding="utf-8")
        data = RuleLoader._parse(text, path.suffix.lower())
        data = RuleLoader._flatten_rule_sets(data)
        return RulePack(**data)

    @staticmethod
    def loads(text: str, format: str = ".yaml") -> RulePack:
        """Load a RulePack from a raw string."""
        data = RuleLoader._parse(text, format.lower())
        data = RuleLoader._flatten_rule_sets(data)
        return RulePack(**data)

    @staticmethod
    def _parse(text: str, suffix: str) -> Any:
        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(text)
        if suffix == ".json":
            return json.loads(text)
        raise ValueError(f"Unsupported rule file format: {suffix}")

    @staticmethod
    def _flatten_rule_sets(data: dict[str, Any]) -> dict[str, Any]:
        """Split rule_sets into applicability_rules and rules; never flatten into scored list."""
        if not isinstance(data, dict) or "rule_sets" not in data:
            return data
        rule_sets = data["rule_sets"]
        applicability = rule_sets.get("applicability") if isinstance(rule_sets, dict) else []
        controls = rule_sets.get("controls") if isinstance(rule_sets, dict) else []
        result = {
            **data,
            "applicability_rules": applicability or [],
            "rules": controls or [],
        }
        result.pop("rule_sets", None)
        return result
