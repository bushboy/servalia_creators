from thebe_core.models import (
    AuditEvent,
    Customer,
    CustomerWorkspace,
    Document,
    EntityContext,
    EvaluationResult,
    OnboardingSchema,
    Provenance,
    Question,
    QuestionCatalog,
    Rule,
    RulePack,
    RuleResult,
    Template,
    Violation,
)


def test_entity_context():
    ctx = EntityContext(entity_type="company", attributes={"name": "Acme"})
    assert ctx.entity_type == "company"
    assert ctx.attributes["name"] == "Acme"


def test_rule_pack():
    rule = Rule(
        rule_id="r001",
        description="Require lawful basis for data processing.",
        severity="high",
        recommended_actions=["Document lawful basis"],
    )
    pack = RulePack(vertical="test", rules=[rule])
    assert pack.vertical == "test"
    assert len(pack.rules) == 1


def test_evaluation_result():
    result = EvaluationResult(
        vertical="test",
        entity_type="company",
        score=0.85,
    )
    assert result.score == 0.85
    assert result.violations == []


def test_rule_result_statuses():
    result = RuleResult(
        rule_id="r1",
        status="PASS",
        control_key="c1",
        source_fields=["context.product"],
        evidence_ids=["e1"],
    )
    assert result.status == "PASS"


def test_audit_event_defaults():
    event = AuditEvent(
        vertical="test",
        customer_id="cust-001",
        action="onboard",
    )
    assert event.event_id
    assert event.timestamp
    assert event.action == "onboard"


def test_document_and_template():
    template = Template(name="summary", format="markdown", content="# {{ title }}")
    doc = Document(vertical="test", format="markdown", content=template.content)
    assert doc.format == "markdown"
    assert template.name == "summary"


def test_customer_workspace():
    customer = Customer(
        customer_id="c1",
        tenant_id="t1",
        vertical="test",
        name="Acme",
    )
    ws = CustomerWorkspace(customer=customer)
    assert ws.customer.customer_id == "c1"
    assert ws.evaluation_count == 0


def test_question_catalog():
    catalog = QuestionCatalog(
        vertical="test",
        profile=[Question(key="company_name", title="Company name")],
        checklist=[Question(control_key="pci_scope_determined", title="PCI scope")],
    )
    assert catalog.profile[0].key == "company_name"
    assert catalog.checklist[0].control_key == "pci_scope_determined"


def test_onboarding_schema():
    schema = OnboardingSchema(vertical="test", json_schema={"fields": []})
    assert schema.vertical == "test"


def test_provenance():
    p = Provenance(actor_id="u1", tenant_id="t1")
    assert p.actor_id == "u1"


def test_violation():
    v = Violation(rule_id="r1", severity="high")
    assert v.rule_id == "r1"
