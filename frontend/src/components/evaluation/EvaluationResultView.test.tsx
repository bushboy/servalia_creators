import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EvaluationResultView } from '@/components/evaluation/EvaluationResultView';
import type { EvaluationResult } from '@/types';

const result: EvaluationResult = {
  evaluation_id: 'e1',
  vertical: 'creator_publishing',
  entity_type: 'asset',
  score: null,
  rule_results: [
    {
      rule_id: 'r1',
      control_key: 'voice_match',
      status: 'UNKNOWN',
      severity: 'medium',
      description: 'Voice match not assessed',
      recommended_actions: [],
      source_fields: ['voice_match'],
      evidence_ids: [],
    },
    {
      rule_id: 'r2',
      control_key: 'no_unverified_guarantee',
      status: 'FAIL',
      severity: 'high',
      description: 'Unverified sales guarantee',
      recommended_actions: ['Remove or qualify the claim'],
      source_fields: [],
      evidence_ids: [],
    },
  ],
  violations: [],
  required_actions: [],
};

describe('EvaluationResultView', () => {
  it('renders governance result with Allow / Review / Block labels', () => {
    render(<EvaluationResultView result={result} />);

    expect(screen.getByText('Governance result')).toBeInTheDocument();
    expect(screen.getAllByText('Block').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.getByText('Unverified sales guarantee')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /create a task/i })
    ).not.toBeInTheDocument();
  });
});
