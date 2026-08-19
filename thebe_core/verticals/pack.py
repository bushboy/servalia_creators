from __future__ import annotations

from thebe_core.models import OnboardingSchema, QuestionCatalog, RulePack, Template


class VerticalPack:
    """Loaded contents of a vertical pack."""

    def __init__(
        self,
        name: str,
        description: str,
        rule_pack: RulePack,
        templates: dict[str, Template],
        onboarding_schema: OnboardingSchema,
        question_catalog: QuestionCatalog | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self._rule_pack = rule_pack
        self._templates = templates
        self._onboarding_schema = onboarding_schema
        self._question_catalog = question_catalog

    def get_rule_pack(self) -> RulePack:
        """Return the loaded RulePack."""
        return self._rule_pack

    def get_templates(self) -> dict[str, Template]:
        """Return a mapping of template name to Template."""
        return dict(self._templates)

    def get_onboarding_schema(self) -> OnboardingSchema:
        """Return the onboarding schema for this vertical."""
        return self._onboarding_schema

    def get_question_catalog(self) -> QuestionCatalog | None:
        """Return the founder-facing question catalog for this vertical."""
        return self._question_catalog
