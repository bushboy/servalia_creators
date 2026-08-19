from __future__ import annotations

import pathlib
from pathlib import Path

from thebe_core.models import Template


class TemplateRegistry:
    """Load and serve Jinja2/Markdown document templates for a vertical pack."""

    def __init__(self, templates_dir: str | pathlib.Path | None = None) -> None:
        self._templates: dict[str, Template] = {}
        if templates_dir is not None:
            self.load(templates_dir)

    def load(self, templates_dir: str | pathlib.Path) -> None:
        """Load every template file in the given directory."""
        directory = Path(templates_dir)
        if not directory.exists():
            raise FileNotFoundError(f"Template directory not found: {directory}")

        for path in directory.glob("*"):
            if not path.is_file():
                continue

            name = path.stem
            suffix = path.suffix.lstrip(".")
            fmt = suffix if suffix else "markdown"
            if fmt == "md":
                fmt = "markdown"

            self._templates[name] = Template(
                name=name,
                format=fmt,
                content=path.read_text(encoding="utf-8"),
            )

    def get(self, name: str) -> Template:
        if name not in self._templates:
            raise KeyError(f"Template not found: {name!r}")
        return self._templates[name]

    def list(self) -> list[str]:
        return list(self._templates)
