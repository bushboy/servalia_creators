from __future__ import annotations

import json
import pathlib

import pytest

from thebe_core.documents.generator import DocGenerator
from thebe_core.documents.registry import TemplateRegistry
from thebe_core.models import EvaluationResult, Template, Violation


def test_vertical_pack_registry(tmp_path: pathlib.Path):
    (tmp_path / "report.md").write_text("# {{ evaluation.vertical }}\n", encoding="utf-8")
    registry = TemplateRegistry(tmp_path)
    assert "report" in registry.list()
    assert registry.get("report").format == "markdown"


def test_generate_markdown_from_template(tmp_path: pathlib.Path):
    (tmp_path / "checklist.md").write_text(
        "# Checklist\n{% for v in evaluation.violations %}{{ v.rule_id }}\n{% endfor %}",
        encoding="utf-8",
    )
    registry = TemplateRegistry(tmp_path)
    generator = DocGenerator()
    evaluation = EvaluationResult(
        vertical="test",
        entity_type="asset",
        score=0.85,
        rule_results=[],
        violations=[
            Violation(
                rule_id="CLAIM-001",
                description="Unsupported guarantee.",
                severity="medium",
                recommended_actions=["Rewrite the claim."],
            ),
        ],
        required_actions=["Rewrite the claim."],
    )

    doc = generator.generate(evaluation, registry.get("checklist"))
    assert doc.format == "markdown"
    assert "Checklist" in doc.content
    assert "CLAIM-001" in doc.content


def test_generate_json():
    generator = DocGenerator()
    evaluation = EvaluationResult(
        vertical="test",
        entity_type="asset",
        score=0.9,
        rule_results=[],
        violations=[],
    )
    template = Template(name="json", format="markdown", content="unused")

    doc = generator.generate(evaluation, template, output_format="json")
    assert doc.format == "json"
    data = json.loads(doc.content)
    assert data["vertical"] == "test"
    assert data["score"] == 0.9


def test_unsupported_format_raises():
    generator = DocGenerator()
    evaluation = EvaluationResult(
        vertical="test",
        entity_type="asset",
        score=1.0,
        rule_results=[],
        violations=[],
    )
    template = Template(name="weird", format="html", content="<p>hi</p>")

    with pytest.raises(ValueError):
        generator.generate(evaluation, template)
