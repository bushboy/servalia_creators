import { describe, expect, it } from 'vitest';
import { navLabelsForRoles } from '@/lib/navRoles';

describe('navLabelsForRoles', () => {
  it('viewer sees Home and Library', () => {
    const labels = navLabelsForRoles(['viewer']);
    expect(labels).toEqual(['Home', 'Library']);
    for (const forbidden of [
      'Audit',
      'Settings',
      'Tenants',
      'Verticals',
      'Findings',
      'Tasks',
      'Documents',
    ]) {
      expect(labels).not.toContain(forbidden);
    }
  });

  it('operator sees Home, Library, and Audit', () => {
    const labels = navLabelsForRoles(['operator']);
    expect(labels).toEqual(['Home', 'Library', 'Audit']);
    expect(labels).not.toContain('Settings');
    expect(labels).not.toContain('Tenants');
  });

  it('admin sees Settings and Tenants after author nav', () => {
    expect(navLabelsForRoles(['admin'])).toEqual([
      'Home',
      'Library',
      'Audit',
      'Settings',
      'Tenants',
    ]);
  });
});
