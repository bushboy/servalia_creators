from __future__ import annotations

import json
import pathlib
from typing import Any

import yaml

from thebe_core.documents.registry import TemplateRegistry
from thebe_core.models import OnboardingSchema, QuestionCatalog, RulePack, Template
from thebe_core.policy.loader import RuleLoader
from thebe_core.verticals.pack import VerticalPack


class VerticalLoader:
    """Load a vertical pack from `verticals/<name>/`."""

    @staticmethod
    def load(pack_path: str | pathlib.Path) -> VerticalPack:
        """Load a pack from an explicit directory path."""
        path = pathlib.Path(pack_path).resolve()
        directory_name = path.name

        meta = VerticalLoader._load_meta(path)
        pack_name = meta.get("name", directory_name)
        pack_description = meta.get("description", "")

        rule_pack = VerticalLoader._load_rules(path)
        templates = VerticalLoader._load_templates(path)
        onboarding_schema = VerticalLoader._load_onboarding(path)
        question_catalog = VerticalLoader._load_questions(path)

        return VerticalPack(
            name=pack_name,
            description=pack_description,
            rule_pack=rule_pack,
            templates=templates,
            onboarding_schema=onboarding_schema,
            question_catalog=question_catalog,
        )

    @classmethod
    def load_by_name(
        cls,
        name: str,
        root: str | pathlib.Path | None = None,
    ) -> VerticalPack:
        """Load a pack by name from a verticals root directory."""
        if root is None:
            root = pathlib.Path(__file__).parents[2] / "verticals"
        return cls.load(pathlib.Path(root) / name)

    @staticmethod
    def _load_meta(path: pathlib.Path) -> dict[str, Any]:
        for filename in ("pack.yaml", "pack.yml", "pack.json"):
            meta_path = path / filename
            if not meta_path.exists():
                continue
            text = meta_path.read_text(encoding="utf-8")
            if meta_path.suffix == ".json":
                return json.loads(text)
            return yaml.safe_load(text) or {}
        return {}

    @staticmethod
    def _load_rules(path: pathlib.Path) -> RulePack:
        for filename in ("rules.yaml", "rules.yml", "rules.json"):
            rules_path = path / filename
            if not rules_path.exists():
                continue
            return RuleLoader.load(rules_path)
        return RulePack(vertical=path.name)

    @staticmethod
    def _load_templates(path: pathlib.Path) -> dict[str, Template]:
        templates_dir = path / "templates"
        if not templates_dir.exists():
            return {}
        registry = TemplateRegistry(templates_dir)
        return {name: registry.get(name) for name in registry.list()}

    @staticmethod
    def _load_onboarding(path: pathlib.Path) -> OnboardingSchema:
        onboarding_path = path / "onboarding_schema.json"
        if not onboarding_path.exists():
            return OnboardingSchema(vertical=path.name)
        data = json.loads(onboarding_path.read_text(encoding="utf-8"))
        if "vertical" not in data:
            data["vertical"] = path.name
        return OnboardingSchema(**data)

    @staticmethod
    def _load_questions(path: pathlib.Path) -> QuestionCatalog | None:
        for filename in ("questions.yaml", "questions.yml", "questions.json"):
            questions_path = path / filename
            if not questions_path.exists():
                continue
            text = questions_path.read_text(encoding="utf-8")
            if questions_path.suffix == ".json":
                data = json.loads(text)
            else:
                data = yaml.safe_load(text) or {}
            if "vertical" not in data:
                data["vertical"] = path.name
            return QuestionCatalog(**data)
        return None
