from __future__ import annotations

import json

from jinja2 import Environment, select_autoescape

from thebe_core.models import Document, EvaluationResult, Template


class DocGenerator:
    """Generate reports from EvaluationResults using Jinja2 templates or JSON."""

    def __init__(self, extra_filters: dict[str, object] | None = None) -> None:
        self.env = Environment(
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        if extra_filters:
            self.env.filters.update(extra_filters)

    def generate(
        self,
        evaluation: EvaluationResult,
        template: Template,
        output_format: str | None = None,
    ) -> Document:
        """Render a Document in the requested format."""
        fmt = output_format or template.format

        if fmt == "json":
            content = json.dumps(
                evaluation.model_dump(mode="json"), indent=2
            )
        elif fmt in {"markdown", "md"}:
            jinja_template = self.env.from_string(template.content)
            content = jinja_template.render(evaluation=evaluation)
        else:
            raise ValueError(f"Unsupported document format: {fmt!r}")

        return Document(
            vertical=evaluation.vertical,
            format=fmt,
            content=content,
        )
