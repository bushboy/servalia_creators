import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { EvaluationResult, RuleResult } from '@/types';

function gapRuleResults(result: EvaluationResult | null): RuleResult[] {
  if (!result?.rule_results?.length) {
    return (result?.violations || []).map((v) => ({
      rule_id: v.rule_id,
      control_key: v.control_key ?? null,
      obligation_key: v.obligation_key,
      status: 'FAIL' as const,
      severity: v.severity,
      description: v.description,
      recommended_actions: v.recommended_actions,
      source_fields: v.source_fields || [],
      evidence_ids: v.evidence_ids || [],
    }));
  }
  return result.rule_results.filter(
    (r) => r.status === 'FAIL' || r.status === 'PARTIAL'
  );
}

interface EvaluationResultViewProps {
  result: EvaluationResult;
}

const STATUS_VARIANT: Record<
  RuleResult['status'],
  'default' | 'secondary' | 'destructive' | 'outline'
> = {
  PASS: 'default',
  PARTIAL: 'secondary',
  FAIL: 'destructive',
  NOT_APPLICABLE: 'outline',
  UNKNOWN: 'outline',
};

const STATUS_LABEL: Record<RuleResult['status'], string> = {
  PASS: 'Allow',
  PARTIAL: 'Review',
  FAIL: 'Block',
  NOT_APPLICABLE: 'Not applicable',
  UNKNOWN: 'Unknown',
};

function overallStatus(rules: RuleResult[]): RuleResult['status'] | null {
  if (!rules.length) return null;
  const rank: RuleResult['status'][] = [
    'FAIL',
    'PARTIAL',
    'UNKNOWN',
    'PASS',
    'NOT_APPLICABLE',
  ];
  return rank.find((status) => rules.some((rule) => rule.status === status)) ?? null;
}

export function EvaluationResultView({ result }: EvaluationResultViewProps) {
  const rules = result.rule_results || [];
  const gaps = gapRuleResults(result);
  const headline = overallStatus(rules);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Governance result</h2>
        <div className="mt-2 flex items-center gap-2">
          {headline ? (
            <Badge variant={STATUS_VARIANT[headline]}>{STATUS_LABEL[headline]}</Badge>
          ) : (
            <span className="text-sm text-muted-foreground">Not assessed yet.</span>
          )}
        </div>
      </div>

      {rules.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Rule results ({rules.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {rules.map((rule) => (
              <div key={rule.rule_id} className="rounded-lg border p-3">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <Badge variant={STATUS_VARIANT[rule.status]}>
                    {STATUS_LABEL[rule.status]}
                  </Badge>
                  <span className="font-medium text-sm">
                    {rule.description || rule.rule_id}
                  </span>
                </div>
                {rule.control_key ? (
                  <p className="text-xs text-muted-foreground">{rule.control_key}</p>
                ) : null}
                {rule.recommended_actions.length > 0 && (
                  <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
                    {rule.recommended_actions.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {rules.length === 0 && gaps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Gaps ({gaps.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {gaps.map((gap) => (
              <div key={gap.rule_id} className="rounded-lg border p-3">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <Badge variant={STATUS_VARIANT[gap.status]}>
                    {STATUS_LABEL[gap.status]}
                  </Badge>
                  <span className="font-medium text-sm">
                    {gap.description || gap.rule_id}
                  </span>
                </div>
                {gap.recommended_actions.length > 0 && (
                  <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
                    {gap.recommended_actions.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {result.required_actions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Required actions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-inside list-disc text-sm text-muted-foreground">
              {result.required_actions.map((action, idx) => (
                <li key={idx}>{action}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {rules.length === 0 &&
        gaps.length === 0 &&
        result.required_actions.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No rule results or required actions for this assessment.
          </p>
        )}
    </div>
  );
}
